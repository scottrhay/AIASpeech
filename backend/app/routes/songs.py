from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Song, Style
import requests
import os
import html  # [SEC-003 FIX] For SSML injection prevention
import time  # [EDGE-003 FIX] For retry backoff

bp = Blueprint('songs', __name__)


def _synthesize_voice_clip(song):
    """Synthesize voice clip using Azure TTS API."""
    azure_speech_key = os.getenv('AZURE_SPEECH_KEY')
    azure_speech_region = os.getenv('AZURE_SPEECH_REGION', 'eastus2')

    if not azure_speech_key:
        raise Exception('Azure Speech API key is not configured. Please contact the administrator.')

    # Get text and voice name
    text = song.specific_lyrics
    if not text or not text.strip():
        raise Exception('Speaker text is required for voice clip synthesis.')

    voice_name = song.voice_name or 'en-US-AndrewMultilingualNeural'

    # Azure TTS endpoint
    tts_endpoint = f'https://{azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1'

    # [SEC-003 FIX] Escape text to prevent SSML injection
    safe_text = html.escape(text)

    # Build SSML
    ssml = f'''<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice_name}'>
            {safe_text}
        </voice>
    </speak>'''

    headers = {
        'Ocp-Apim-Subscription-Key': azure_speech_key,
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
    }

    # [EDGE-003 FIX] Retry with exponential backoff for 429 rate limits
    max_retries = 3
    retry_delay = 2  # seconds, doubles each retry

    try:
        response = None
        for attempt in range(max_retries + 1):
            current_app.logger.info(f"Synthesizing voice clip for song {song.id} with voice {voice_name} (attempt {attempt + 1})")
            response = requests.post(tts_endpoint, data=ssml.encode('utf-8'), headers=headers, timeout=60)

            # Log the status code for debugging
            current_app.logger.info(f"Azure TTS API Status: {response.status_code}")

            # Handle specific HTTP error codes
            if response.status_code == 401:
                raise Exception('Azure Speech API authentication failed.')
            elif response.status_code == 403:
                raise Exception('Azure Speech API access denied.')
            elif response.status_code == 429:
                if attempt < max_retries:
                    wait = retry_delay * (2 ** attempt)
                    current_app.logger.warning(f"Azure TTS 429 rate limit — retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait)
                    continue
                else:
                    raise Exception('Rate limit exceeded after retries. Please try again later.')
            elif response.status_code >= 500:
                raise Exception('Azure Speech API is currently unavailable.')
            else:
                break  # Success or other client error

        response.raise_for_status()

        # Save audio to a file
        import uuid
        from pathlib import Path

        # Create audio directory if it doesn't exist
        audio_dir = Path('/app/static/audio')
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        filename = f"{song.id}_{uuid.uuid4().hex[:8]}.mp3"
        filepath = audio_dir / filename

        # Write audio file
        with open(filepath, 'wb') as f:
            f.write(response.content)

        # Set download URL
        app_url = os.getenv('APP_URL', 'https://speech.aiacopilot.com')
        song.download_url_1 = f"{app_url}/static/audio/{filename}"
        song.status = 'completed'
        db.session.commit()

        current_app.logger.info(f"Voice clip synthesized successfully for song {song.id}: {song.download_url_1}")
        return {'status': 'completed', 'url': song.download_url_1}

    except requests.exceptions.Timeout:
        raise Exception('Request timed out. Please try again.')
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Azure TTS error: {str(e)}")
        raise Exception(f'Failed to synthesize voice clip: {str(e)}')


@bp.route('/', methods=['GET'])
@jwt_required()
def get_songs():
    """Get all songs with filtering and search."""
    user_id = get_jwt_identity()

    # Get query parameters
    status = request.args.get('status')
    voice_name = request.args.get('voice_name')
    search = request.args.get('search')
    show_all_users = request.args.get('all_users', 'false').lower() == 'true'

    # Build query
    query = Song.query

    # Filter by user unless show_all_users is true
    if not show_all_users:
        query = query.filter_by(user_id=user_id)

    # Apply filters
    if status and status != 'all':
        query = query.filter_by(status=status)

    if voice_name:
        query = query.filter_by(voice_name=voice_name)

    # Apply search
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Song.specific_title.like(search_pattern),
                Song.specific_lyrics.like(search_pattern)
            )
        )

    # Order by creation date (newest first)
    query = query.order_by(Song.created_at.desc())

    songs = query.all()

    return jsonify({
        'songs': [song.to_dict(include_user=show_all_users, include_style=True) for song in songs],
        'total': len(songs)
    }), 200


@bp.route('/<int:song_id>', methods=['GET'])
@jwt_required()
def get_song(song_id):
    """Get a specific song."""
    song = Song.query.get(song_id)

    if not song:
        return jsonify({'error': 'Song not found'}), 404

    return jsonify({'song': song.to_dict(include_user=True, include_style=True)}), 200


@bp.route('/', methods=['POST'])
@jwt_required()
def create_song():
    """Create a new song."""
    user_id = get_jwt_identity()
    data = request.get_json()

    # Validate style exists if provided
    if data.get('style_id'):
        style = Style.query.get(data['style_id'])
        if not style:
            return jsonify({'error': 'Style not found'}), 404

    # Create song
    song = Song(
        user_id=user_id,
        specific_title=data.get('specific_title'),
        version=data.get('version', 'v1'),
        specific_lyrics=data.get('specific_lyrics'),
        prompt_to_generate=data.get('prompt_to_generate'),
        style_id=data.get('style_id'),
        vocal_gender=data.get('vocal_gender'),
        voice_name=data.get('voice_name'),
        status=data.get('status', 'create')
    )

    try:
        db.session.add(song)
        db.session.commit()

        # Synthesize voice clip using Azure TTS
        if song.status == 'create':
            try:
                _synthesize_voice_clip(song)
            except Exception as api_error:
                # Log the error
                current_app.logger.error(f"Failed to synthesize voice clip: {api_error}")
                # Mark as failed instead of rolling back
                song.status = 'failed'
                db.session.commit()
                return jsonify({'error': str(api_error)}), 500

        return jsonify({
            'message': 'Voice clip created successfully' if song.status == 'completed' else 'Voice clip created',
            'song': song.to_dict(include_user=True, include_style=True)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:song_id>', methods=['PUT'])
@jwt_required()
def update_song(song_id):
    """Update an existing song."""
    user_id = get_jwt_identity()
    song = Song.query.get(song_id)

    if not song:
        return jsonify({'error': 'Song not found'}), 404

    # Check ownership
    if song.user_id != user_id:
        return jsonify({'error': 'Unauthorized to update this song'}), 403

    data = request.get_json()

    # Validate style if provided
    if data.get('style_id'):
        style = Style.query.get(data['style_id'])
        if not style:
            return jsonify({'error': 'Style not found'}), 404

    # Update fields
    if 'specific_title' in data:
        song.specific_title = data['specific_title']
    if 'specific_lyrics' in data:
        song.specific_lyrics = data['specific_lyrics']
    if 'prompt_to_generate' in data:
        song.prompt_to_generate = data['prompt_to_generate']
    if 'style_id' in data:
        song.style_id = data['style_id']
    if 'vocal_gender' in data:
        song.vocal_gender = data['vocal_gender']
    if 'voice_name' in data:
        song.voice_name = data['voice_name']
    if 'status' in data:
        song.status = data['status']
    if 'star_rating' in data:
        # Validate star_rating is between 0 and 5
        rating = data['star_rating']
        if not isinstance(rating, int) or rating < 0 or rating > 5:
            return jsonify({'error': 'Star rating must be between 0 and 5'}), 400
        song.star_rating = rating
    if 'downloaded_url_1' in data:
        song.downloaded_url_1 = bool(data['downloaded_url_1'])
    if 'downloaded_url_2' in data:
        song.downloaded_url_2 = bool(data['downloaded_url_2'])

    try:
        db.session.commit()
        return jsonify({
            'message': 'Song updated successfully',
            'song': song.to_dict(include_user=True, include_style=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:song_id>/recreate', methods=['POST'])
@jwt_required()
def recreate_song(song_id):
    """Recreate/regenerate an existing song."""
    user_id = get_jwt_identity()
    song = Song.query.get(song_id)

    if not song:
        return jsonify({'error': 'Song not found'}), 404

    # Check ownership
    if song.user_id != user_id:
        return jsonify({'error': 'Unauthorized to recreate this song'}), 403

    try:
        # Reset download URLs and submit to Azure Speech
        song.download_url_1 = None
        song.download_url_2 = None
        song.status = 'create'

        # Access style relationship before commit to ensure it's loaded
        _ = song.style

        db.session.commit()

        # Synthesize voice clip using Azure TTS
        _synthesize_voice_clip(song)

        return jsonify({
            'message': 'Voice clip regenerated successfully',
            'song': song.to_dict(include_user=True, include_style=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in recreate_song: {str(e)}", exc_info=True)
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500


@bp.route('/<int:song_id>', methods=['DELETE'])
@jwt_required()
def delete_song(song_id):
    """Delete a song."""
    user_id = get_jwt_identity()
    song = Song.query.get(song_id)

    if not song:
        return jsonify({'error': 'Song not found'}), 404

    # Check ownership
    if song.user_id != user_id:
        return jsonify({'error': 'Unauthorized to delete this song'}), 403

    try:
        db.session.delete(song)
        db.session.commit()
        return jsonify({'message': 'Song deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Get song statistics."""
    user_id = get_jwt_identity()
    show_all_users = request.args.get('all_users', 'false').lower() == 'true'

    # Build base query
    base_query = Song.query if show_all_users else Song.query.filter_by(user_id=user_id)

    # Count completed songs that actually have audio files
    completed_with_audio = base_query.filter(
        Song.status == 'completed',
        db.or_(Song.download_url_1.isnot(None), Song.download_url_2.isnot(None))
    ).count()

    stats = {
        'total': base_query.count(),
        'create': base_query.filter_by(status='create').count(),
        'submitted': base_query.filter_by(status='submitted').count(),
        'completed': completed_with_audio,
        'failed': base_query.filter_by(status='failed').count(),
        'unspecified': base_query.filter_by(status='unspecified').count()
    }

    return jsonify(stats), 200

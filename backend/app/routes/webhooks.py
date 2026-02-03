from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import Song
import json
import os
import hmac

bp = Blueprint('webhooks', __name__)


def _verify_webhook_secret():
    """[SEC-002 FIX] Verify webhook secret header to prevent unauthenticated callbacks.
    If WEBHOOK_SECRET env var is set, the caller must provide it in X-Webhook-Secret header."""
    secret = os.getenv('WEBHOOK_SECRET')
    if not secret:
        # No secret configured — allow (backward compatible, log warning)
        current_app.logger.warning("WEBHOOK_SECRET not set — webhook endpoint is unauthenticated!")
        return True
    provided = request.headers.get('X-Webhook-Secret', '')
    return hmac.compare_digest(secret, provided)


@bp.route('/azure-speech-callback', methods=['POST'])
def azure_speech_callback():
    """
    Webhook endpoint for Azure Speech API callbacks.

    Handles multiple possible payload formats from Azure Speech API:

    Format 1 (expected):
    {
        "task_id": "xxx",
        "status": "completed",
        "msg": "All generated successfully.",
        "data": [
            {"audio_url": "url1", "title": "title1", "image_url": "..."},
            {"audio_url": "url2", "title": "title2", "image_url": "..."}
        ]
    }

    Format 2 (alternative):
    {
        "taskId": "xxx",
        "status": "success",
        "data": {
            "songs": [...]
        }
    }
    """
    # [SEC-002 FIX] Verify webhook secret before processing
    if not _verify_webhook_secret():
        current_app.logger.warning("Azure Speech callback: Invalid or missing webhook secret")
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    # Log the raw callback for debugging
    current_app.logger.info(f"Azure Speech callback received: {json.dumps(data, indent=2)}")

    if not data:
        current_app.logger.error("Azure Speech callback: No data received")
        return jsonify({'error': 'No data received'}), 400

    # Extract task_id (try multiple possible field names and locations)
    task_id = data.get('task_id') or data.get('taskId') or data.get('id')

    # Also check if it's nested in a data object
    if not task_id and 'data' in data and isinstance(data['data'], dict):
        task_id = data['data'].get('task_id') or data['data'].get('taskId')

    if not task_id:
        current_app.logger.error(f"Azure Speech callback: No task_id found in payload: {data}")
        return jsonify({'error': 'task_id is required'}), 400

    # Find song by speech task ID
    song = Song.query.filter_by(speech_task_id=task_id).first()

    if not song:
        current_app.logger.error(f"Azure Speech callback: No song found for task_id: {task_id}")
        return jsonify({'error': f'Song not found for task_id: {task_id}'}), 404

    current_app.logger.info(f"Azure Speech callback: Found song {song.id} for task_id {task_id}")

    # Check status (handle multiple possible status indicators)
    status = data.get('status', '').lower()
    msg = data.get('msg', '') or data.get('message', '')

    is_success = (
        status in ['completed', 'success', 'done'] or
        'successfully' in msg.lower() or
        'complete' in msg.lower()
    )

    # Handle failure status
    if status in ['failed', 'error', 'failure']:
        song.status = 'failed'
        current_app.logger.error(f"Azure Speech callback: Song {song.id} generation failed: {msg}")
        try:
            db.session.commit()
            return jsonify({
                'message': 'Song marked as failed',
                'error': msg
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Extract audio data (handle multiple possible structures)
    audio_data = data.get('data', [])

    # If data is a dict with nested songs/clips/data array
    if isinstance(audio_data, dict):
        audio_data = (
            audio_data.get('data') or  # API format: data.data.data[]
            audio_data.get('songs') or
            audio_data.get('clips') or
            audio_data.get('results') or
            []
        )

    # Ensure it's a list
    if not isinstance(audio_data, list):
        audio_data = [audio_data] if audio_data else []

    current_app.logger.info(f"Azure Speech callback: Found {len(audio_data)} audio items")

    if is_success and audio_data:
        song.status = 'completed'

        # Extract audio URLs (try multiple possible field names)
        if len(audio_data) > 0:
            item = audio_data[0]
            song.download_url_1 = (
                item.get('audio_url') or
                item.get('audioUrl') or
                item.get('url') or
                item.get('audio')
            )
            current_app.logger.info(f"Azure Speech callback: download_url_1 = {song.download_url_1}")

        if len(audio_data) > 1:
            item = audio_data[1]
            song.download_url_2 = (
                item.get('audio_url') or
                item.get('audioUrl') or
                item.get('url') or
                item.get('audio')
            )
            current_app.logger.info(f"Azure Speech callback: download_url_2 = {song.download_url_2}")

        try:
            db.session.commit()
            current_app.logger.info(f"Azure Speech callback: Song {song.id} updated successfully")
            return jsonify({
                'message': 'Song updated successfully',
                'song': song.to_dict(include_user=True, include_style=True)
            }), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Azure Speech callback: Database error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    else:
        # Log but still return 200 to acknowledge receipt
        current_app.logger.warning(f"Azure Speech callback: Unexpected payload for song {song.id}: is_success={is_success}, audio_data_len={len(audio_data)}")
        return jsonify({
            'message': 'Callback received but no audio data found',
            'status_received': status,
            'msg_received': msg
        }), 200


@bp.route('/test', methods=['GET', 'POST'])
def test_webhook():
    """
    Test endpoint to verify webhook is accessible.
    GET: Returns simple status
    POST: Logs the payload and returns it
    """
    if request.method == 'GET':
        return jsonify({'status': 'ok', 'message': 'Webhook endpoint is accessible'}), 200

    data = request.get_json()
    current_app.logger.info(f"Test webhook received: {json.dumps(data, indent=2) if data else 'No data'}")
    return jsonify({
        'status': 'ok',
        'received': data
    }), 200

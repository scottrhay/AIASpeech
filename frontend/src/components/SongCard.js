import React from 'react';
import './SongCard.css';

function SongCard({ song, onView, onDelete, onDuplicate }) {
  const getStatusClass = (status) => {
    switch (status) {
      case 'create':
        return 'status-create';
      case 'submitted':
        return 'status-submitted';
      case 'completed':
        return 'status-completed';
      case 'failed':
        return 'status-failed';
      default:
        return 'status-unspecified';
    }
  };

  const getStatusLabel = (status) => {
    return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unspecified';
  };

  const truncateText = (text, maxLength = 150) => {
    if (!text) return 'No lyrics provided';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="song-card" onClick={() => onView(song)}>
      <div className="song-card-header">
        <div className="song-icon">♫</div>
        <div className="header-right">
          {song.status === 'submitted' && (
            <span className="status-badge status-submitted">Generating...</span>
          )}
          {song.status === 'failed' && (
            <span className="status-badge status-failed">Failed</span>
          )}
          <div className="card-actions" onClick={(e) => e.stopPropagation()}>
            <button
              className="icon-btn icon-duplicate"
              onClick={() => onDuplicate(song)}
              title="Duplicate"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
            <button
              className="icon-btn icon-delete"
              onClick={() => onDelete(song.id)}
              title="Delete"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                <line x1="10" y1="11" x2="10" y2="17"></line>
                <line x1="14" y1="11" x2="14" y2="17"></line>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div className="song-card-body">
        <h3 className="song-title">
          {song.specific_title || 'Untitled Song'}
        </h3>

        <p className="song-lyrics">{truncateText(song.specific_lyrics)}</p>

        {/* Show audio players and download links for completed songs */}
        {/* [EDGE-001 FIX] Use .trim() to handle empty string URLs */}
        {song.status === 'completed' && ((song.download_url_1 && song.download_url_1.trim()) || (song.download_url_2 && song.download_url_2.trim())) && (
          <div className="song-audio-section" onClick={(e) => e.stopPropagation()}>
            {song.download_url_1 && song.download_url_1.trim() && (
              <div className="audio-track">
                <div className="audio-header">
                  <span className="track-label">Version 1</span>
                  <a
                    href={song.download_url_1}
                    download
                    className="download-link"
                    title="Download Version 1"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                  </a>
                </div>
                {/* [EDGE-002 FIX] Add error handler for audio load failures */}
                <audio controls className="audio-player" onError={(e) => { e.target.parentElement.querySelector('.audio-error')?.classList.remove('hidden'); }}>
                  <source src={song.download_url_1} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
                <span className="audio-error hidden" style={{color: '#ef4444', fontSize: '0.75rem'}}>⚠ Audio unavailable</span>
              </div>
            )}
            {song.download_url_2 && song.download_url_2.trim() && (
              <div className="audio-track">
                <div className="audio-header">
                  <span className="track-label">Version 2</span>
                  <a
                    href={song.download_url_2}
                    download
                    className="download-link"
                    title="Download Version 2"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                      <polyline points="7 10 12 15 17 10"></polyline>
                      <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                  </a>
                </div>
                {/* [EDGE-002 FIX] Add error handler for audio load failures */}
                <audio controls className="audio-player" onError={(e) => { e.target.parentElement.querySelector('.audio-error')?.classList.remove('hidden'); }}>
                  <source src={song.download_url_2} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
                <span className="audio-error hidden" style={{color: '#ef4444', fontSize: '0.75rem'}}>⚠ Audio unavailable</span>
              </div>
            )}
          </div>
        )}

        <div className="song-meta">
          {song.creator && (
            <div className="meta-item">
              <span className="meta-label">Creator:</span>
              <span className="meta-value">{song.creator}</span>
            </div>
          )}
          {song.style_name && (
            <div className="meta-item">
              <span className="meta-label">Style:</span>
              <span className="meta-value">{song.style_name}</span>
            </div>
          )}
          {song.vocal_gender && (
            <div className="meta-item">
              <span className="meta-label">Vocal:</span>
              <span className="meta-value">
                {song.vocal_gender.charAt(0).toUpperCase() + song.vocal_gender.slice(1)}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SongCard;

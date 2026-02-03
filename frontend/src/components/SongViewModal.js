import React from 'react';
import './SongViewModal.css';

function SongViewModal({ song, onClose, onDuplicate }) {
  if (!song) return null;

  const getStatusLabel = (status) => {
    return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unspecified';
  };

  const handleDuplicate = () => {
    onDuplicate(song);
    onClose();
  };

  const handleDownload = async (url, filename) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);

      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up the blob URL
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('Download failed:', error);
      // Fallback to opening in new tab
      window.open(url, '_blank');
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content view-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            {song.specific_title || 'Untitled Song'}
            {song.version && <span className="song-version-badge">{song.version}</span>}
          </h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="view-modal-body">
          <div className="view-row">
            {song.style_name && (
              <div className="view-section">
                <label className="view-label">Style</label>
                <div className="view-value">{song.style_name}</div>
              </div>
            )}

            {song.vocal_gender && (
              <div className="view-section">
                <label className="view-label">Vocal Gender</label>
                <div className="view-value">
                  {song.vocal_gender.charAt(0).toUpperCase() + song.vocal_gender.slice(1)}
                </div>
              </div>
            )}
          </div>

          {song.specific_lyrics && (
            <div className="view-section">
              <label className="view-label">Lyrics</label>
              <div className="view-value lyrics-content">{song.specific_lyrics}</div>
            </div>
          )}

          {song.prompt_to_generate && (
            <div className="view-section">
              <label className="view-label">Prompt to Generate</label>
              <div className="view-value">{song.prompt_to_generate}</div>
            </div>
          )}

          {song.creator && (
            <div className="view-section">
              <label className="view-label">Creator</label>
              <div className="view-value">{song.creator}</div>
            </div>
          )}

          {/* [EDGE-001 FIX] Use .trim() to handle empty string URLs */}
          {((song.download_url_1 && song.download_url_1.trim()) || (song.download_url_2 && song.download_url_2.trim())) && (
            <div className="view-section">
              <label className="view-label">Audio</label>
              <div className="audio-players">
                {song.download_url_1 && song.download_url_1.trim() && (
                  <div className="audio-track">
                    <div className="audio-header">
                      <span className="track-label">Version 1</span>
                      <button
                        className="download-link-icon"
                        title="Download Version 1"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload(
                            song.download_url_1,
                            `${(song.specific_title || 'song').replace(/[/\\?%*:|"<>]/g, '-')}_1_${song.version || 'v1'}.mp3`
                          );
                        }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <polyline points="7 10 12 15 17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </div>
                    {/* [EDGE-002 FIX] Add error handler for audio load failures */}
                    <audio controls className="audio-player" style={{ width: '100%' }} onError={(e) => { e.target.parentElement.querySelector('.audio-error')?.classList.remove('hidden'); }}>
                      <source src={song.download_url_1} type="audio/mpeg" />
                      Your browser does not support the audio element.
                    </audio>
                    <span className="audio-error hidden" style={{color: '#ef4444', fontSize: '0.75rem'}}>⚠ Audio file unavailable or expired</span>
                  </div>
                )}
                {song.download_url_2 && song.download_url_2.trim() && (
                  <div className="audio-track">
                    <div className="audio-header">
                      <span className="track-label">Version 2</span>
                      <button
                        className="download-link-icon"
                        title="Download Version 2"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload(
                            song.download_url_2,
                            `${(song.specific_title || 'song').replace(/[/\\?%*:|"<>]/g, '-')}_2_${song.version || 'v1'}.mp3`
                          );
                        }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <polyline points="7 10 12 15 17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </div>
                    {/* [EDGE-002 FIX] Add error handler for audio load failures */}
                    <audio controls className="audio-player" style={{ width: '100%' }} onError={(e) => { e.target.parentElement.querySelector('.audio-error')?.classList.remove('hidden'); }}>
                      <source src={song.download_url_2} type="audio/mpeg" />
                      Your browser does not support the audio element.
                    </audio>
                    <span className="audio-error hidden" style={{color: '#ef4444', fontSize: '0.75rem'}}>⚠ Audio file unavailable or expired</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
          >
            Close
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleDuplicate}
          >
            Duplicate
          </button>
        </div>
      </div>
    </div>
  );
}

export default SongViewModal;

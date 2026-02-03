import React, { useState } from 'react';
import './SongCardEnhanced.css';

function SongCardEnhanced({ song, onView, onDelete, onDuplicate }) {
  const [isHovered, setIsHovered] = useState(false);

  const getStatusBadge = (status) => {
    const badges = {
      'completed': { label: 'Ready', className: 'status-ready' },
      'submitted': { label: 'Generating', className: 'status-generating' },
      'create': { label: 'Draft', className: 'status-draft' },
      'failed': { label: 'Failed', className: 'status-failed' },
    };
    return badges[status] || { label: 'Unknown', className: 'status-unknown' };
  };

  const truncateText = (text, maxLength = 120) => {
    if (!text) return 'No lyrics provided';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const statusBadge = getStatusBadge(song.status);
  // [EDGE-001 FIX] Use .trim() to handle empty string URLs
  const hasAudio = song.status === 'completed' && ((song.download_url_1 && song.download_url_1.trim()) || (song.download_url_2 && song.download_url_2.trim()));

  return (
    <div
      className={`song-card-enhanced ${isHovered ? 'song-card-enhanced--hovered' : ''}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onView(song)}
    >
      {/* Status Badge */}
      <div className={`song-card-enhanced__status ${statusBadge.className}`}>
        {statusBadge.label}
        {song.status === 'submitted' && (
          <span className="status-indicator"></span>
        )}
      </div>

      {/* Header */}
      <div className="song-card-enhanced__header">
        <div className="track-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M9 18V5L21 3V16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <circle cx="6" cy="18" r="3" stroke="currentColor" strokeWidth="2"/>
            <circle cx="18" cy="16" r="3" stroke="currentColor" strokeWidth="2"/>
          </svg>
        </div>

        {/* Hover Actions */}
        <div className="song-card-enhanced__actions" onClick={(e) => e.stopPropagation()}>
          {hasAudio && (
            <button
              className="action-btn action-btn--play"
              onClick={(e) => {
                e.stopPropagation();
                onView(song);
              }}
              title="Play"
              aria-label="Play song"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 5V19L19 12L8 5Z" fill="currentColor"/>
              </svg>
            </button>
          )}

          <button
            className="action-btn action-btn--duplicate"
            onClick={(e) => {
              e.stopPropagation();
              onDuplicate(song);
            }}
            title="Duplicate"
            aria-label="Duplicate song"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke="currentColor" strokeWidth="2"/>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </button>

          <button
            className="action-btn action-btn--delete"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(song.id);
            }}
            title="Delete"
            aria-label="Delete song"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="3 6 5 6 21 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="song-card-enhanced__body">
        <h3 className="track-title">
          {song.specific_title || 'Untitled Song'}
        </h3>

        <p className="track-lyrics">
          {truncateText(song.specific_lyrics)}
        </p>

        {/* Audio Player Preview (for completed songs) */}
        {hasAudio && (
          <div className="track-audio-preview" onClick={(e) => e.stopPropagation()}>
            <audio controls className="audio-player-mini">
              <source src={song.download_url_1 || song.download_url_2} type="audio/mpeg" />
            </audio>
          </div>
        )}

        {/* Metadata Row */}
        <div className="track-metadata">
          {song.creator && (
            <div className="meta-item">
              <svg width="14" height="14" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 15C6 13.3431 7.34315 12 9 12H11C12.6569 12 14 13.3431 14 15M11.5 6.5C11.5 7.88071 10.3807 9 9 9C7.61929 9 6.5 7.88071 6.5 6.5C6.5 5.11929 7.61929 4 9 4C10.3807 4 11.5 5.11929 11.5 6.5Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>{song.creator}</span>
            </div>
          )}

          {song.style_name && (
            <div className="meta-item">
              <svg width="14" height="14" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 3L12 7H16L13 10L14 14L10 11L6 14L7 10L4 7H8L10 3Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>{song.style_name}</span>
            </div>
          )}

          {song.vocal_gender && (
            <div className="meta-item">
              <svg width="14" height="14" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 14C12 13.47 11.789 12.961 11.414 12.586C11.039 12.211 10.53 12 10 12C9.47 12 8.961 12.211 8.586 12.586C8.211 12.961 8 13.47 8 14M10 8V2M6 6L10 2L14 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span>{song.vocal_gender.charAt(0).toUpperCase() + song.vocal_gender.slice(1)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SongCardEnhanced;

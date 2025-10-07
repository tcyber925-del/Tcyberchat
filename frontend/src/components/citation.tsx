import React from 'react';
import { Citation as CitationType } from '@/types/message';

interface CitationProps {
  citation: CitationType;
  onClick: (docId: string, page?: number) => void;
}

const Citation: React.FC<CitationProps> = ({ citation, onClick }) => {
  const handleClick = () => {
    onClick(citation.docId, citation.page);
  };

  return (
    <sup
      className="cursor-pointer text-blue-600 hover:underline"
      onClick={handleClick}
      title={citation.snippet}
    >
      [{citation.id}]
    </sup>
  );
};

export default Citation;
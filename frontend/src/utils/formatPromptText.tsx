import React from 'react';

export function formatPromptText(text: string | null): React.ReactNode {
  if (!text) return null;

  // Normalize whitespace while preserving paragraph structure
  const normalizedText = text.replace(/[ \t]+/g, ' ').trim();
  
  // Split by double line breaks to identify paragraphs
  const paragraphs = normalizedText.split(/\n\n+/);
  
  return paragraphs.map((paragraph, paragraphIndex) => {
    const lines = paragraph.split('\n').filter(line => line.trim());
    
    // Check if this paragraph contains list items
    const isListParagraph = lines.some(line => 
      line.trim().startsWith('- ') || line.trim().startsWith('• ')
    );
    
    if (isListParagraph) {
      const listItems: string[] = [];
      const regularLines: string[] = [];
      
      lines.forEach(line => {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('• ')) {
          listItems.push(trimmedLine.substring(2).trim());
        } else if (trimmedLine) {
          regularLines.push(trimmedLine);
        }
      });
      
      return (
        <div key={paragraphIndex} className="mb-3 last:mb-0">
          {regularLines.length > 0 && (
            <p className="mb-2 last:mb-0">
              {regularLines.join(' ')}
            </p>
          )}
          {listItems.length > 0 && (
            <ul className="list-disc pl-5 space-y-1.5">
              {listItems.map((item, itemIndex) => (
                <li key={itemIndex} className="break-words">
                  {item}
                </li>
              ))}
            </ul>
          )}
        </div>
      );
    } else {
      // Regular paragraph
      const paragraphText = lines.join(' ');
      return paragraphText && (
        <p key={paragraphIndex} className="mb-3 last:mb-0 break-words">
          {paragraphText}
        </p>
      );
    }
  });
}
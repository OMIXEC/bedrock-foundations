"""
Ticket Category Badge Component

Displays the detected ticket category with color-coded styling.
Categories: BILLING (blue), TECHNICAL (red), ACCOUNT (yellow), GENERAL (gray)
"""

interface TicketCategoryProps {
  category: string;
}

export default function TicketCategory({ category }: TicketCategoryProps) {
  const getCategoryStyle = () => {
    switch (category) {
      case 'BILLING':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'TECHNICAL':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'ACCOUNT':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'GENERAL':
        return 'bg-gray-100 text-gray-800 border-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getCategoryIcon = () => {
    switch (category) {
      case 'BILLING':
        return '💳';
      case 'TECHNICAL':
        return '🔧';
      case 'ACCOUNT':
        return '👤';
      case 'GENERAL':
        return '💬';
      default:
        return '❓';
    }
  };

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-medium">
      <span className={`inline-flex items-center gap-2 ${getCategoryStyle()}`}>
        <span>{getCategoryIcon()}</span>
        <span>{category}</span>
      </span>
    </div>
  );
}

export function describeFreshness(updatedAt: string | null): string {
  if (!updatedAt) return "No recent pedestrian data available.";
  const updated = new Date(updatedAt).getTime();
  if (Number.isNaN(updated)) return "No recent pedestrian data available.";
  const minutesAgo = Math.max(0, Math.round((Date.now() - updated) / 60000));
  if (minutesAgo === 0) return "Data updated just now.";
  if (minutesAgo === 1) return "Data updated 1 minute ago.";
  return `Data updated ${minutesAgo} minutes ago.`;
}

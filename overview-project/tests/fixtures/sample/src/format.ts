export const MAX_LENGTH = 40;
export function formatName(name: string): string {
  return name.trim().slice(0, MAX_LENGTH);
}

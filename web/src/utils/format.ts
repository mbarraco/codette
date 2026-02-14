export function truncateUuid(uuid: string, len = 8): string {
  return uuid.slice(0, len);
}

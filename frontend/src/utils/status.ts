/**
 * Status conversion utilities for bridging frontend and backend status representations.
 *
 * Frontend uses '1' (enabled) / '2' (disabled) strings.
 * Backend uses boolean true (enabled) / false (disabled).
 */

/** Convert backend boolean/string to frontend EnableStatus string */
export function booleanToEnableStatus(value: boolean | string | null | undefined): Api.Common.EnableStatus {
  if (value === null || value === undefined) return '1';
  if (typeof value === 'string') return value === '1' ? '1' : '2';
  return value ? '1' : '2';
}

/** Convert frontend EnableStatus string (or boolean) to backend boolean */
export function enableStatusToBoolean(value: string | boolean | null | undefined): boolean {
  if (value === null || value === undefined) return true;
  return typeof value === 'boolean' ? value : value === '1';
}

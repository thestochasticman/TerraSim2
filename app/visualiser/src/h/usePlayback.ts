import { useCallback, useEffect, useState } from "react";

export const FRAME_MS = 80;

/**
 * What the hook exposes.
 *
 * day : the day the user is on, or null to follow the newest written day
 * setDay : jump to a day; stops playback
 * playing : whether the timer is advancing the day
 * togglePlay : start or stop; starting from the last day restarts at zero
 */
export type Playback = {
  day: number | null;
  setDay: (day: number | null) => void;
  playing: boolean;
  togglePlay: () => void;
};

/**
 * Own the scrubber's position and play timer.
 *
 * nDays : dimensionless
 *     Days available to play through. Playback stops on the last one.
 * enabled : whether scrubbing and playing are allowed (false while a run is still writing)
 * frameMs : milliseconds between days while playing
 *
 * Disabling resets to following the newest day. While playing, the day
 * advances every frameMs and playback stops at nDays - 1.
 */
export function usePlayback(nDays: number, enabled: boolean, frameMs: number = FRAME_MS): Playback {
  const [day, setDayState] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);

  const setDay = useCallback((next: number | null) => {
    setPlaying(false);
    setDayState(next === null ? null : Math.min(Math.max(0, next), Math.max(0, nDays - 1)));
  }, [nDays]);

  const togglePlay = useCallback(() => {
    if (!enabled || nDays === 0) return;
    if (playing) {
      setPlaying(false);
      return;
    }
    setDayState((d) => (d === null || d >= nDays - 1 ? 0 : d));
    setPlaying(true);
  }, [enabled, nDays, playing]);

  useEffect(() => {
    if (!enabled) {
      const id = setTimeout(() => {
        setPlaying(false);
        setDayState(null);
      }, 0);
      return () => clearTimeout(id);
    }
  }, [enabled]);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setDayState((d) => {
        const next = (d ?? -1) + 1;
        if (next >= nDays - 1) {
          setPlaying(false);
          return nDays - 1;
        }
        return next;
      });
    }, frameMs);
    return () => clearInterval(id);
  }, [playing, nDays, frameMs]);

  return { day, setDay, playing, togglePlay };
}

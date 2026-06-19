import { inBounds, isInWater, isOnLand, snapToWater, distanceKm } from './geo-region';

describe('geo-region (real OSM coastline)', () => {
  describe('inBounds', () => {
    it('accepts a point inside the archipelago', () => {
      expect(inBounds(48.55, -123.05)).toBe(true);
    });

    it('rejects a point far south (Tacoma / MaST Center)', () => {
      expect(inBounds(47.349, -122.325)).toBe(false);
    });

    it('rejects non-finite input', () => {
      expect(inBounds(NaN, -123.0)).toBe(false);
    });
  });

  describe('isOnLand', () => {
    it('flags Friday Harbor town interior on San Juan Island', () => {
      expect(isOnLand(48.534, -123.013)).toBe(true);
    });

    it('does not flag open water (Haro Strait)', () => {
      expect(isOnLand(48.55, -123.22)).toBe(false);
    });
  });

  describe('isInWater', () => {
    it('is true for open Haro Strait water', () => {
      expect(isInWater(48.55, -123.22)).toBe(true);
    });

    it('is false out of region even if not on land', () => {
      expect(isInWater(47.349, -122.325)).toBe(false);
    });
  });

  describe('snapToWater', () => {
    it('leaves an in-water point unchanged', () => {
      const p = snapToWater(48.55, -123.22);
      expect(p.lat).toBeCloseTo(48.55, 5);
      expect(p.lng).toBeCloseTo(-123.22, 5);
    });

    it('moves a known on-land point (Friday Harbor interior) into water', () => {
      expect(isOnLand(48.534, -123.013)).toBe(true);
      const snapped = snapToWater(48.534, -123.013);
      expect(isInWater(snapped.lat, snapped.lng)).toBe(true);
    });

    it('places the Lime Kiln shoreline seed in water', () => {
      // Lime Kiln Point sits on the west shore of San Juan Island. Whether the
      // simplified ring treats it as land or water, it must end up in water.
      const snapped = snapToWater(48.5158, -123.1526);
      expect(isInWater(snapped.lat, snapped.lng)).toBe(true);
    });
  });

  describe('seed sighting points are in or snappable to water', () => {
    const seeds: ReadonlyArray<readonly [string, number, number]> = [
      ['Salmon Bank', 48.5847, -123.0731],
      ['Hein Bank', 48.6542, -123.0289],
      ['Rosario Strait', 48.5789, -122.9876],
      ['President Channel', 48.6123, -123.0456],
      ['Spieden Channel', 48.6234, -123.1567]
    ];

    seeds.forEach(([name, lat, lng]) => {
      it(`${name} ends up in water`, () => {
        const snapped = snapToWater(lat, lng);
        expect(isInWater(snapped.lat, snapped.lng)).toBe(true);
      });
    });
  });

  describe('distanceKm', () => {
    it('computes a sane great-circle distance', () => {
      const d = distanceKm({ lat: 48.5, lng: -123.0 }, { lat: 48.6, lng: -123.0 });
      expect(d).toBeGreaterThan(10);
      expect(d).toBeLessThan(13);
    });
  });
});

export type Point = [number, number];

export function pointInPolygon(point: Point, polygon: Point[]): boolean {
  const [x, y] = point;
  let inside = false;
  for (let i = 0; i < polygon.length; i += 1) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[(i + 1) % polygon.length];
    if (yi > y !== yj > y) {
      const xinters = ((xj - xi) * (y - yi)) / (yj - yi) + xi;
      if (x < xinters) {
        inside = !inside;
      }
    }
  }
  return inside;
}

function onSegment(a: Point, b: Point, c: Point): boolean {
  return (
    Math.min(a[0], b[0]) <= c[0] &&
    c[0] <= Math.max(a[0], b[0]) &&
    Math.min(a[1], b[1]) <= c[1] &&
    c[1] <= Math.max(a[1], b[1])
  );
}

function orientation(a: Point, b: Point, c: Point): number {
  const value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1]);
  if (value === 0) {
    return 0;
  }
  return value > 0 ? 1 : 2;
}

function segmentsIntersect(p1: Point, q1: Point, p2: Point, q2: Point): boolean {
  const o1 = orientation(p1, q1, p2);
  const o2 = orientation(p1, q1, q2);
  const o3 = orientation(p2, q2, p1);
  const o4 = orientation(p2, q2, q1);
  if (o1 !== o2 && o3 !== o4) {
    return true;
  }
  if (o1 === 0 && onSegment(p1, q1, p2)) {
    return true;
  }
  if (o2 === 0 && onSegment(p1, q1, q2)) {
    return true;
  }
  if (o3 === 0 && onSegment(p2, q2, p1)) {
    return true;
  }
  if (o4 === 0 && onSegment(p2, q2, q1)) {
    return true;
  }
  return false;
}

export function polygonsIntersect(poly1: Point[], poly2: Point[]): boolean {
  if (poly1.length < 3 || poly2.length < 3) {
    return false;
  }
  for (let i = 0; i < poly1.length; i += 1) {
    const a = poly1[i];
    const b = poly1[(i + 1) % poly1.length];
    for (let j = 0; j < poly2.length; j += 1) {
      const c = poly2[j];
      const d = poly2[(j + 1) % poly2.length];
      if (segmentsIntersect(a, b, c, d)) {
        return true;
      }
    }
  }
  if (pointInPolygon(poly1[0], poly2) || pointInPolygon(poly2[0], poly1)) {
    return true;
  }
  return false;
}

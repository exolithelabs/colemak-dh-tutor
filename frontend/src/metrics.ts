export function calculateAccuracy(current: string, target: string): number {
  if (!current.length) return 100;
  let correct = 0;
  for (let index = 0; index < current.length; index += 1) {
    if (current[index] === target[index]) correct += 1;
  }
  return Math.round(correct / current.length * 100);
}

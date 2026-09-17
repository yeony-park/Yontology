import { formatName } from '../src/format';
test('formats a name', () => {
  expect(formatName(' Ada ')).toBe('Ada');
});

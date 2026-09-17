import Button from './Button';
import { formatName } from './format';
import './styles.css';

export function App() {
  const title = formatName(' Overview ');
  return <main className="app flex gap-4"><Button label={title} /></main>;
}

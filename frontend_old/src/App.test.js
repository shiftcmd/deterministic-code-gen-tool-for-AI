import { render, screen } from '@testing-library/react';

// Simple test that doesn't require complex dependencies
test('React Testing Library is working', () => {
  // Test that React Testing Library can render a simple component
  render(<div data-testid="test">Hello Jest!</div>);
  
  const element = screen.getByTestId('test');
  expect(element).toBeInTheDocument();
  expect(element).toHaveTextContent('Hello Jest!');
});

test('DOM matchers are working', () => {
  render(
    <div>
      <button disabled>Disabled Button</button>
      <input value="test" readOnly />
    </div>
  );
  
  const button = screen.getByRole('button');
  const input = screen.getByRole('textbox');
  
  expect(button).toBeDisabled();
  expect(input).toHaveValue('test');
}); 
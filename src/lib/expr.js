// A small arithmetic evaluator for the browser, matching the `derive`
// expressions that validate.py evaluates: numbers, + - * / **, parentheses,
// names, and calls such as M('H2O'). Nothing else is accepted.

const TOKEN = /\s*(?:(\d+\.?\d*(?:e[-+]?\d+)?|\.\d+)|([A-Za-z_]\w*)|'([^']*)'|(\*\*|[-+*/(),]))/y;

/** "36.0 / M('H2O')" -> [{type:'num'}, {type:'op'}, {type:'name'}, ...] */
export function tokenize(expression) {
  const tokens = [];
  let at = 0;
  while (at < expression.length) {
    TOKEN.lastIndex = at;
    const m = TOKEN.exec(expression);
    if (!m) break;
    if (m[1] != null) tokens.push({ type: 'num', text: m[1], value: Number(m[1]) });
    else if (m[2] != null) tokens.push({ type: 'name', value: m[2] });
    else if (m[3] != null) tokens.push({ type: 'str', value: m[3] });
    else tokens.push({ type: 'op', value: m[4] });
    at = TOKEN.lastIndex;
  }
  if (expression.slice(at).trim()) throw new Error(`cannot read ${JSON.stringify(expression.slice(at))}`);
  return tokens;
}

/** Evaluate an expression. env = { names: {x: 1}, functions: {M: fn} } */
export function evaluate(expression, { names = {}, functions = {} } = {}) {
  const tokens = tokenize(expression);
  let i = 0;
  const peek = () => tokens[i]?.value;
  const take = (value) => {
    if (peek() !== value) throw new Error(`expected ${value} in ${expression}`);
    i++;
  };

  function primary() {
    const token = tokens[i++];
    if (!token) throw new Error(`unfinished expression: ${expression}`);
    if (token.type === 'num' || token.type === 'str') return token.value;
    if (token.type === 'name') {
      if (peek() !== '(') {
        if (!(token.value in names)) throw new Error(`unknown name ${token.value}`);
        return names[token.value];
      }
      if (!(token.value in functions)) throw new Error(`unknown function ${token.value}`);
      take('(');
      const args = [];
      while (peek() !== ')') {
        args.push(sum());
        if (peek() === ',') i++;
      }
      take(')');
      return functions[token.value](...args);
    }
    if (token.value === '(') {
      const value = sum();
      take(')');
      return value;
    }
    throw new Error(`unexpected ${token.value} in ${expression}`);
  }
  // As in Python, ** binds tighter than a minus sign on its left.
  const power = () => {
    const left = primary();
    if (peek() !== '**') return left;
    i++;
    return left ** unary();
  };
  const unary = () => (peek() === '-' ? (i++, -unary()) : power());
  const product = () => {
    let value = unary();
    while (peek() === '*' || peek() === '/') value = tokens[i++].value === '*' ? value * unary() : value / unary();
    return value;
  };
  function sum() {
    let value = product();
    while (peek() === '+' || peek() === '-') value = tokens[i++].value === '+' ? value + product() : value - product();
    return value;
  }

  const result = sum();
  if (i < tokens.length) throw new Error(`unexpected ${peek()} in ${expression}`);
  return result;
}

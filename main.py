class LL1Parser:
    def __init__(self, grammar, start_symbol):
        self.grammar = self.read_grammar(grammar)
        self.start_symbol = start_symbol
        self.non_terminals, self.terminals = self.find_non_terminals_and_terminals()
        self.first_sets = self.compute_first_sets()
        self.follow_sets = self.compute_follow_sets()
        self.parsing_table = self.construct_parsing_table()

    def read_grammar(self, grammar_str):
        rules = {}
        productions = grammar_str.strip().split('\n')
        for prod in productions:
            lhs, rhs = prod.split('->')
            lhs, rhs = lhs.strip(), rhs.strip().split('|')
            rhs = [tuple(alt.strip().split()) for alt in rhs]
            rules[lhs] = rhs
        return rules

    def find_non_terminals_and_terminals(self):
        non_terminals = set(self.grammar.keys())
        terminals = {symbol for rhs in self.grammar.values() for prod in rhs for symbol in prod if symbol not in non_terminals}
        terminals.discard('ε')
        return non_terminals, terminals

    def compute_first_sets(self):
        first = {nt: set() for nt in self.non_terminals}
        changed = True

        while changed:
            changed = False
            for nt in self.non_terminals:
                for prod in self.grammar[nt]:
                    # Empty production
                    if prod == ('ε',):
                        if 'ε' not in first[nt]:
                            first[nt].add('ε')
                            changed = True
                    else:
                        # Non-empty production
                        for symbol in prod:
                            if symbol in self.terminals:
                                if symbol not in first[nt]:
                                    first[nt].add(symbol)
                                    changed = True
                                break
                            else:
                                # Add FIRST(symbol) to FIRST(nt)
                                for f in first[symbol]:
                                    if f != 'ε' and f not in first[nt]:
                                        first[nt].add(f)
                                        changed = True
                                if 'ε' not in first[symbol]:
                                    break
        return first

    def compute_follow_sets(self):
        follow = {nt: set() for nt in self.non_terminals}
        follow[self.start_symbol].add('$')  # Add end-of-input marker to FOLLOW(start_symbol)
        changed = True

        while changed:
            changed = False
            for nt in self.non_terminals:
                for prod in self.grammar[nt]:
                    tail_follow = follow[nt]
                    for symbol in reversed(prod):
                        if symbol in self.non_terminals:
                            size_before = len(follow[symbol])
                            follow[symbol] |= tail_follow
                            if 'ε' in self.first_sets[symbol]:
                                tail_follow = tail_follow | (self.first_sets[symbol] - {'ε'})
                            else:
                                tail_follow = self.first_sets[symbol]
                            size_after = len(follow[symbol])
                            if size_before != size_after:
                                changed = True
                        else:
                            tail_follow = {symbol} if symbol != 'ε' else set()

        return follow

    def construct_parsing_table(self):
        table = {}
        for nt in self.non_terminals:
            for t in self.terminals.union({'$'}):
                table[(nt, t)] = []
        for nt in self.non_terminals:
            for prod in self.grammar[nt]:
                if prod == ('ε',):
                    for f in self.follow_sets[nt]:
                        table[(nt, f)] = ['ε']
                else:
                    first = self.compute_first_of_sequence(prod)
                    for f in first - {'ε'}:
                        table[(nt, f)] = list(prod)
                    if 'ε' in first:
                        for f in self.follow_sets[nt]:
                            table[(nt, f)] = list(prod)

        return table

    def compute_first_of_sequence(self, sequence):
        if sequence[0] == 'ε':
            return {'ε'}
        elif sequence[0] in self.terminals:
            return {sequence[0]}
        else:
            result = set()
            for symbol in sequence:
                if symbol in self.terminals:
                    result.add(symbol)
                    break
                result |= self.first_sets[symbol]
                if 'ε' not in self.first_sets[symbol]:
                    result.discard('ε')
                    break
            else:
                result.add('ε')
            return result

    def parse(self, input_string):
        # Tokenize the input_string here. For simplicity, let's assume it's already a list of tokens.
        tokens = input_string.split() + ['$']  # Add end-of-input marker

        # Initialize stack with start symbol
        stack = [self.start_symbol]

        # Initialize pointer to the first token
        token_index = 0

        while stack:
            print(f"Stack: {stack}, Next token: {tokens[token_index]}")  # Debugging print
            # Look at the top of the stack
            top = stack[-1]
            current_token = tokens[token_index]

            if top in self.terminals:
                # If the top of the stack is a terminal, consume the token
                if top == current_token:
                    stack.pop()  # Pop the matched terminal
                    token_index += 1  # Move to the next token
                else:
                    # Terminal doesn't match token; this is a syntax error
                    raise SyntaxError(f"Syntax error: expected {top}, got {current_token}")
            elif top in self.non_terminals:
                # If the top of the stack is a non-terminal, consult the parsing table
                if self.parsing_table[(top, current_token)]:
                    stack.pop()  # Pop the non-terminal
                    # Push the production onto the stack in reverse order
                    production = self.parsing_table[(top, current_token)]
                    if production != ['ε']:  # Check if production is not epsilon before pushing
                        stack.extend(reversed(production))
                else:
                    # There's no production for this non-terminal and token; this is a syntax error
                    expected = self.expected_tokens(top)
                    raise SyntaxError(f"Syntax error: expected one of {expected}, got {current_token}")
            elif top == '$':
                # If the end-of-input marker is at the top, the input should be fully consumed
                if current_token == '$':
                    break  # Successfully parsed
                else:
                    # Input not fully consumed; this is a syntax error
                    raise SyntaxError(f"Syntax error: unexpected token {current_token}, expected end of input")

            print(f"Updated Stack: {stack}")  # Debugging print after stack update

        if token_index < len(tokens) - 1:
            # If there are still tokens but the stack is empty, this is a syntax error
            raise SyntaxError(f"Syntax error: unexpected token {tokens[token_index]}, expected end of input")

        # If we exit the loop without errors, the input is successfully parsed
        print("Parsing completed successfully.")

    def expected_tokens(self, non_terminal):
        expected = set()
        for symbol in self.terminals.union({'$'}):
            if self.parsing_table[(non_terminal, symbol)]:
                expected.add(symbol)
        return expected

# Example grammar and usage
grammar = """
E -> T E'
E' -> + T E' | ε
T -> F T'
T' -> * F T' | ε
F -> ( E ) | id
"""

parser = LL1Parser(grammar, 'E')
parser.parse("id + id * id")

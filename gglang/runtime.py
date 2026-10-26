import re
import sys

# 원소: 엄(부호) 0개 이상 + 숫자/변수/입력
ATOM = re.compile(r"(엄*)((?:아뇨)+|쥐~+랄|\x01)")
INT_IN = "\x01"   # 아 예?


class GGError(Exception):
    def __init__(self, line_no, msg):
        super().__init__(f"{line_no}번째 줄: {msg}")


class GGya:
    def __init__(self):
        self.vars = {}
        self.lines = []
        self.pair = {}
        self.outer = {}
        self.no = 0           # 지금 보고 있는 줄 번호 (에러 메시지용)

    def error(self, msg):
        raise GGError(self.no, msg)

    def type(self, line):
        s = line.rstrip(" ")
        if s == "":
            return "EMPTY"
        if re.fullmatch(r"요이~+", s):
            return "LOOP"
        if s == "줴줴이야" or s.startswith("줴줴이야 "):
            return "BREAK"
        if s == "티~원":
            return "SPACE"
        if s.startswith("티~원 "):
            return "NUM"
        if s == "티~~원":
            return "NEWLINE"
        if s.startswith("티~~원 "):
            return "CHAR"
        if re.match(r"쥐~+랄 ", s):
            return "VAR"
        return "UNKNOWN"

    def check(self):
        stack = []
        for i, line in enumerate(self.lines):
            self.no = i + 1
            s = line.rstrip(" ")
            t = self.type(line)
            if t == "UNKNOWN":
                if re.fullmatch(r"쥐~+랄", s):
                    self.error("대입할 값이 없음")
                self.error(f"모르는 명령 '{s}'")
            elif t == "LOOP":
                n = s.count("~")
                if stack and stack[-1][0] == n:
                    _, open_i = stack.pop()
                    self.pair[open_i] = i
                    self.pair[i] = open_i
                elif any(m == n for m, _ in stack):
                    self.error(f"요이{'~' * n} 짝이 엇갈림")
                else:
                    stack.append((n, i))
            elif t == "BREAK":
                self.outer[i] = stack[-1][1] if stack else None
                if s != "줴줴이야":
                    self.syntax(s[5:])
            elif t == "NUM":
                self.syntax(s[4:])
            elif t == "CHAR":
                self.syntax(s[5:])
            elif t == "VAR":
                self.syntax(s.split(" ", 1)[1])
        if stack:
            n, open_i = stack[0]
            self.no = open_i + 1
            self.error(f"요이{'~' * n} 짝이 없음")

    def syntax(self, expr):
        """식 구문만 검사한다. 틀리면 GGError."""
        expr = expr.strip(" ")
        if "\t" in expr:
            self.error("탭은 들여쓰기에만 쓸 수 있음")
        while expr.startswith("엄 "):
            expr = expr[2:].strip(" ")
        if expr in ("", "엄"):
            self.error("'엄' 뒤에 값이 없음")
        if re.search(r"아 예\?{2,}", expr):
            self.error("'아 예' 뒤 물음표는 1개만")
        expr = expr.replace("아 예?", INT_IN)
        for term in expr.split(" "):
            if term == "":
                continue
            if term == "엄":
                self.error("부정 '엄'은 식 맨 앞에만 쓸 수 있음")
            pos = 0
            while pos < len(term):
                m = ATOM.match(term, pos)
                if m:
                    pos = m.end()
                    continue
                rest = term[pos:].lstrip("엄")
                if rest == "":
                    self.error("'엄' 뒤에 값이 없음")
                self.error(f"식에 쓸 수 없는 글자 '{rest[0]}'")

    def run(self, code):
        self.lines = []
        for raw in code.split("\n"):
            raw = raw.removesuffix("\r")
            self.lines.append(raw.lstrip(" \t"))
        self.check()
        i = 0
        while i < len(self.lines):
            self.no = i + 1
            line = self.lines[i]
            s = line.rstrip(" ")
            t = self.type(line)
            if t == "SPACE":
                print(" ", end="")
            elif t == "CHAR":
                n = self.value(s[5:])
                if not (0 <= n <= 0x10FFFF) or 0xD800 <= n <= 0xDFFF:
                    self.error(f"문자로 바꿀 수 없는 수 '{n}'")
                print(chr(n), end="")
            elif t == "NEWLINE":
                print()
            elif t == "NUM":
                print(self.value(s[4:]), end="")
            elif t == "VAR":
                name, expr = s.split(" ", 1)
                self.vars[name.count("~")] = self.value(expr)
            elif t == "LOOP":
                if self.pair[i] < i:
                    i = self.pair[i]
            elif t == "BREAK":
                expr = s[5:]
                if expr == "" or self.value(expr) == 0:
                    if self.outer[i] is None:
                        return
                    i = self.pair[self.outer[i]]
            i += 1

    def read(self):
        line = sys.stdin.readline()
        if line == "":
            self.error("입력이 없음")
        return line.removesuffix("\n").removesuffix("\r")

    def value(self, expr):
        expr = expr.strip(" ")
        if expr.startswith("엄 "):
            return 1 if self.value(expr[2:]) == 0 else 0
        expr = expr.replace("아 예?", INT_IN)
        result = 1
        for term in expr.split(" "):
            if term == "":
                continue
            total = 0
            for signs, atom in ATOM.findall(term):
                if atom.startswith("쥐"):
                    n = self.vars.get(atom.count("~"), 0)
                elif atom == INT_IN:
                    line = self.read()
                    if not re.fullmatch(r"[+-]?[0-9]+", line.strip(" ")):
                        self.error(f"정수가 아님 '{line}'")
                    n = int(line.strip(" "))
                else:
                    n = atom.count("아뇨")
                if len(signs) % 2:
                    n = -n
                total += n
            result *= total
        return result

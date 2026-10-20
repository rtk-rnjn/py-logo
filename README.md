# Logo Interpreter & Turtle Graphics Engine

A lightweight, sandboxed Python interpreter and vector-to-PNG rendering engine for the Logo programming language. Basically a knock-off version of MSW-Logo.

If you want to copy this repo DO IT.

## Installation

### Prerequisites

- [lark](https://github.com/lark-parser/lark)
- [Pillow](https://pillow.readthedocs.io/en/stable/)

```bash
pip install lark Pillow
```

## Quick Start

### Basic Usage: Drawing a Square

```python
from __future__ import annotations

from src import LogoInterpreter, LogoParser

raw_code = """
FD 100
RT 90
FD 100
RT 90
FD 100
RT 90
FD 100
"""

code = LogoParser().parse(raw_code)

interpreter = LogoInterpreter()
interpreter.execute(code)

image_buffer = interpreter.turtle.render()

with open("output.png", "wb") as f:
    f.write(image_buffer.getvalue())
```

### Advanced Example: Procedures, Variables & Colors

```python
from src import LogoInterpreter, LogoParser
from src.turtle import Turtle

logo_program = """
; Define a recursive spiral procedure
TO SPIRAL :SIZE :ANGLE :STEPS
  REPEAT :STEPS [
    FD :SIZE
    RT :ANGLE
    MAKE :SIZE :SIZE + 3
  ]
END

CS
SETWIDTH 3
SETPC "#FF5733
PU
SETXY -50 -50
PD
SPIRAL 10 91 60
"""

ast = LogoParser().parse(logo_program)

# pass a custom-sized Turtle instance (default is 1000x800)
custom_turtle = Turtle(width=1200, height=900)
interpreter = LogoInterpreter(turtle=custom_turtle)
interpreter.execute(ast)

with open("spiral.png", "wb") as f:
    f.write(interpreter.turtle.render().getvalue())
```

### Variables, Control Flow & Procedures

#### Variables (`MAKE`)

```logo
MAKE :SIDE 120
FD :SIDE
MAKE :SIDE :SIDE + 20
```

#### Loops (`REPEAT`)

```logo
REPEAT 4 [
  FD 100
  RT 90
]
```

#### Procedures (`TO ... END`)

```logo
TO POLYGON :SIDES :LENGTH
  REPEAT :SIDES [
    FD :LENGTH
    RT 360 / :SIDES
  ]
END

POLYGON 6 80
```

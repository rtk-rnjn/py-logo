# Logo Interpreter & Turtle Graphics Engine (`py-logo`)

A lightweight, sandboxed Python interpreter and vector-to-PNG/GIF rendering engine for the [MSWLogo](https://en.wikipedia.org/wiki/MSWLogo) programming language. Built with a zero-dependency Lisp-style tokenizer/reader, an arity-driven evaluator, tail-call optimization, and an isolated subprocess runner designed for Discord bots.

If you want to copy this repo DO IT.

## Installation

### Prerequisites

- Python 3.10+
- [Pillow](https://pillow.readthedocs.io/en/stable/) (no external parser libraries required)

```bash
pip install Pillow
```

## Quick Start

### Basic Usage: Drawing a Square

```python
from __future__ import annotations

from src import LogoInterpreter, LogoParser

raw_code = """
REPEAT 4 [
  FD 100
  RT 90
]
"""

code = LogoParser().parse(raw_code)

interpreter = LogoInterpreter()
interpreter.execute(code)

image_buffer = interpreter.turtle.render()

with open("output.png", "wb") as f:
    f.write(image_buffer.getvalue())
```

### Advanced Example: Procedures, `OUTPUT`, `FILLED` & Custom Canvas

```python
from __future__ import annotations

from src import LogoInterpreter, LogoParser, Turtle

logo_program = """
; Reporter procedure that returns a value with OUTPUT
TO NEXT_SIZE :S
  OUTPUT :S + 3
END

; Tail-recursive spiral procedure (optimized by TCO)
TO SPIRAL :SIZE :ANGLE :STEPS
  IF :STEPS <= 0 [STOP]
  FD :SIZE
  RT :ANGLE
  SPIRAL (NEXT_SIZE :SIZE) :ANGLE :STEPS - 1
END

CS
SETBG [245 247 250]
SETPENSIZE 3
SETPC "#FF5733

; Draw a filled star at the center first
FILLED "GOLD [
  REPEAT 5 [FD 60 RT 144]
]

PU
SETXY -50 -50
PD
SPIRAL 10 91 120
"""

ast = LogoParser().parse(logo_program)

# Pass a custom-sized Turtle instance (default is 1000x800) and optional RNG seed
custom_turtle = Turtle(width=1200, height=900)
interpreter = LogoInterpreter(turtle=custom_turtle, seed=42)
interpreter.execute(ast)

with open("spiral.png", "wb") as f:
    f.write(interpreter.turtle.render().getvalue())
```

### Animated GIF Export

```python
from __future__ import annotations

from src import LogoInterpreter

interpreter = LogoInterpreter()
interpreter.run("""
SETBG "BLACK
SETPENSIZE 2
FOR [I 1 72] [
  SETPC (MODULO :I 15) + 1
  CIRCLE 80
  RT 5
]
""")

gif_buffer = interpreter.turtle.render_gif(max_frames=60, duration_ms=40, scale=0.5)

with open("rosette.gif", "wb") as f:
    f.write(gif_buffer.getvalue())
```

## Discord Bot Integration (Sandboxed Subprocess)

Never run untrusted Logo programs directly on your bot's `asyncio` event loop. Use `run_logo_sandboxed_async` to execute each program in a separate subprocess with OS memory limits (`RLIMIT_AS`), CPU time limits (`RLIMIT_CPU`), a hard wall-clock timeout, and a global concurrency semaphore:

```python
from __future__ import annotations

import asyncio
from io import BytesIO

import discord
from discord.ext import commands

from src import LogoError, run_logo_sandboxed_async

LOGO_SEMAPHORE = asyncio.Semaphore(4)

@bot.command(name="logo")
@commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
async def logo_cmd(ctx: commands.Context, *, code: str) -> None:
    clean_code = (
        code.strip()
        .removeprefix("```logo")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    try:
        result = await run_logo_sandboxed_async(
            clean_code,
            semaphore=LOGO_SEMAPHORE,
            animate_gif=False,
        )
    except LogoError as exc:
        await ctx.reply(f"Logo error: {exc}", mention_author=False)
        return

    ext = "gif" if result.is_gif else "png"
    file = discord.File(BytesIO(result.image_bytes), filename=f"turtle.{ext}")
    caption = "\n".join(result.output[:10]) if result.output else None
    await ctx.reply(content=caption, file=file, mention_author=False)
```

## Language Guide

### Variables & Scoping (`MAKE`, `LOCAL`, `THING`)

Use a quoted word (`"NAME`) when setting a variable with `MAKE`, and `:NAME` (or `THING "NAME`) when reading it:

```logo
MAKE "SIDE 120
FD :SIDE
MAKE "SIDE :SIDE + 20
PRINT THING "SIDE
```

Inside procedures, declare local variables with `LOCAL` or `LOCALMAKE` so they do not overwrite global state:

```logo
TO WALK :DIST
  LOCAL "STEP
  MAKE "STEP :DIST / 4
  REPEAT 4 [FD :STEP RT 15]
END
```

### Control Flow (`REPEAT`, `IF`, `IFELSE`, `FOR`, `WHILE`, `FOREACH`)

```logo
; REPEAT with 1-based REPCOUNT
REPEAT 6 [
  FD REPCOUNT * 15
  RT 60
]

; Conditionals: IF, IFELSE, and TEST / IFTRUE / IFFALSE
IF :SIDE > 100 [SETPC "RED]
IFELSE :SIDE = 140 [FD 50] [BK 50]

TEST :SIDE > 50
IFTRUE [SETPENSIZE 4]
IFFALSE [SETPENSIZE 1]

; FOR [var start end step] [body]
FOR [N 10 100 10] [
  FD :N
  RT 90
]

; WHILE and UNTIL
MAKE "X 80
WHILE [:X > 10] [
  FD :X
  RT 45
  MAKE "X :X - 10
]

; FOREACH over a list or word using ? for the current item
FOREACH [RED GREEN BLUE ORANGE] [
  SETPC ?
  FD 60
  RT 90
]
```

### Procedures & Reporters (`TO ... END`, `OUTPUT`, `STOP`)

Procedures can act as commands or return values using `OUTPUT` (`OP`). Tail-recursive procedures are automatically optimized so they do not exhaust the call-depth limit:

```logo
TO AREA :SIDE
  OUTPUT :SIDE * :SIDE
END

TO POLYGON :SIDES :LENGTH
  REPEAT :SIDES [
    FD :LENGTH
    RT 360 / :SIDES
  ]
END

POLYGON 6 80
FD AREA 5
```

### Parenthesized Variadic Calls

Many built-in primitives accept a variable number of arguments when wrapped in parentheses:

```logo
MAKE "TOTAL (SUM 10 20 30 40 50)
MAKE "ITEMS (LIST 1 2 3 4)
MAKE "COMBINED (SENTENCE [A B] "C [D E])
MAKE "GREETING (WORD "HELLO "_ "WORLD)
MAKE "R (RANDOM 50 100)
(PRINT "Total: :TOTAL "Greeting: :GREETING)
```

### Multiple Turtles (`TELL`, `ASK`, `SETTURTLE`, `WHO`)

Control up to 16 independent turtles sharing the same canvas:

```logo
TELL [0 1 2 3]
ASK 0 [SETH 0 SETPC "RED]
ASK 1 [SETH 90 SETPC "BLUE]
ASK 2 [SETH 180 SETPC "GREEN]
ASK 3 [SETH 270 SETPC "ORANGE]
REPEAT 36 [FD 10 RT 10]
```

## Supported Command Reference

| Category | Commands & Reporters |
| :--- | :--- |
| **Movement & Position** | `FD`/`FORWARD`, `BK`/`BACK`/`BACKWARD`, `RT`/`RIGHT`, `LT`/`LEFT`, `HOME`, `SETXY`, `SETPOS`, `SETX`, `SETY`, `SETH`/`SETHEADING`, `POS`, `XCOR`, `YCOR`, `HEADING`, `TOWARDS`, `DIST`/`DISTANCE` |
| **Pen, Screen & Visibility** | `PU`/`PENUP`, `PD`/`PENDOWN`, `PPT`/`PENPAINT`, `PE`/`PENERASE`, `PX`/`PENREVERSE`, `CS`/`CLEARSCREEN`, `CLEAN`, `ST`/`SHOWTURTLE`, `HT`/`HIDETURTLE`, `SHOWNP`/`SHOWN?`, `PENDOWNP`/`PENDOWN?` |
| **Colors & Pen Size** | `SETPC`/`SETPENCOLOR` (name, `[r g b]`, palette `0..15`, or `#RRGGBB`), `SETFC`/`SETFLOODCOLOR`, `SETBG`/`SETSC`/`SETSCREENCOLOR`, `SETPENSIZE`/`SETWIDTH`/`SETW`, `PENCOLOR`/`PC`, `SCREENCOLOR`/`SC`/`BG`, `PENSIZE` |
| **Shapes, Fills & Text** | `ARC`, `CIRCLE`, `ELLIPSE`, `DOT`, `FILL`, `FILLED`, `LABEL`, `SETLABELHEIGHT`/`SETFONTSIZE` |
| **Control Flow** | `REPEAT`, `REPCOUNT`/`#`, `IF`, `IFELSE`, `TEST`, `IFTRUE`/`IFT`, `IFFALSE`/`IFF`, `FOR`, `WHILE`, `UNTIL`, `FOREACH` (`?`), `RUN`, `STOP`, `OUTPUT`/`OP`, `IGNORE` |
| **Procedures & Variables** | `TO ... END`, `MAKE`, `LOCAL`, `LOCALMAKE`, `THING`, `NAMEP`/`NAME?` |
| **Math & Logic** | Infix `+`, `-`, `*`, `/`, `%`, `^`, `=`, `<>`, `!=`, `<`, `>`, `<=`, `>=`; prefix `SUM`, `DIFFERENCE`, `MINUS`, `PRODUCT`, `QUOTIENT`, `REMAINDER`, `MODULO`, `SQRT`, `POWER`, `EXP`, `LN`, `LOG10`, `SIN`, `COS`, `TAN`, `ARCTAN`, `RADSIN`, `RADCOS`, `RADARCTAN`, `RANDOM`, `RERANDOM`, `INT`, `ROUND`, `ABS`, `SIGN`, `PI`, `EQUALP`, `NOTEQUALP`, `LESSP`, `GREATERP`, `LESSEQUALP`, `GREATEREQUALP`, `AND`, `OR`, `NOT`, `TRUE`, `FALSE` |
| **Words, Lists & Output** | `LIST`, `SENTENCE`/`SE`, `WORD`, `FIRST`, `LAST`, `BUTFIRST`/`BF`, `BUTLAST`/`BL`, `ITEM`, `PICK`, `COUNT`, `FPUT`, `LPUT`, `EMPTYP`, `WORDP`, `LISTP`, `NUMBERP`, `MEMBERP`, `LOWERCASE`, `UPPERCASE`, `ASCII`, `CHAR`, `PRINT`/`PR`, `TYPE`, `SHOW` |
| **Multi-Turtle** | `SETTURTLE`, `TELL`, `ASK`, `WHO`, `TURTLE`, `TURTLES` |

## Safety Limits & Environment Configuration

All execution limits can be customized via environment variables and raise a unified `LogoError` (`LogoRuntimeError` / `LogoSyntaxError`) when exceeded:

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `MAX_SOURCE_LENGTH` | `2000` | Maximum source code length in characters |
| `MAX_NESTING_DEPTH` | `50` | Maximum bracket `[ ... ]` and expression nesting depth |
| `MAX_OPERATIONS` | `200000` | Total evaluation ticks (statements, expressions, operators, and loops) |
| `MAX_REPEAT` | `10000` | Maximum iterations per `REPEAT`, `FOR`, `WHILE`, `UNTIL`, or `FOREACH` loop |
| `MAX_CALL_DEPTH` | `100` | Maximum non-tail procedure recursion depth |
| `MAX_PEN_WIDTH` | `50` | Maximum pen stroke width in pixels |
| `MAX_SEGMENTS` | `20000` | Maximum drawn segments/primitives per canvas |
| `MAX_LIST_LENGTH` | `1000` | Maximum items in a `LogoList` |
| `MAX_WORD_LENGTH` | `500` | Maximum characters in a Logo word |
| `MAX_VARIABLES` | `500` | Maximum variables per environment scope |
| `MAX_PROCEDURES` | `200` | Maximum user-defined procedures |
| `MAX_OUTPUT_LINES` | `200` | Maximum lines captured by `PRINT` / `SHOW` |
| `MAX_FILLS` | `50` | Maximum `FILL` flood-fill operations per program |
| `MAX_TURTLES` | `16` | Maximum concurrent turtles (`0..15`) |
| `MAX_GIF_FRAMES` | `60` | Maximum frames rendered by `render_gif()` |
| `MAX_WALL_TIME_SECONDS` | `3.0` | Subprocess wall-clock timeout in `sandbox.py` |
| `MAX_MEMORY_MB` | `256` | Subprocess address-space cap (`RLIMIT_AS`) in `sandbox.py` |

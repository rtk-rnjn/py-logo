from __future__ import annotations

import unittest

from PIL import Image

from src import (
    LogoInterpreter,
    LogoList,
    LogoParser,
    LogoRuntimeError,
    LogoSyntaxError,
    Turtle,
    parse_color,
)


class TestMSWLogoRewrite(unittest.TestCase):
    def run_code(self, code: str, *, seed: int | None = 42) -> tuple[LogoInterpreter, Turtle]:
        turtle = Turtle()
        interp = LogoInterpreter(turtle=turtle, seed=seed)
        program = LogoParser().parse(code)
        interp.execute(program)
        return interp, turtle

    # 1. Core Grammar Fixes & Arity-Driven Parsing
    def test_arity_driven_minus_disambiguation(self) -> None:
        # `foo 10 -5` is 1 argument (5) if `foo` takes 1 param, or 2 arguments (10, -5) if `foo` takes 2 params!
        code = """
        TO ONE_ARG :A
            MAKE "RES1 :A
        END

        TO TWO_ARGS :A :B
            MAKE "RES2_A :A
            MAKE "RES2_B :B
        END

        ONE_ARG 10 -5
        TWO_ARGS 10 -5
        """
        interp, _ = self.run_code(code)
        self.assertEqual(interp.global_env.get("RES1"), 5.0)
        self.assertEqual(interp.global_env.get("RES2_A"), 10.0)
        self.assertEqual(interp.global_env.get("RES2_B"), -5.0)

    def test_procedure_binary_minus_and_full_expressions(self) -> None:
        code = """
        TO SQUARE :SIDE
            REPEAT 4 [FD :SIDE RT 90]
        END

        TO DEC_TEST :X
            IF :X <= 0 [STOP]
            FD :X
            DEC_TEST :X - 1
        END

        MAKE "X 4
        SQUARE 10 + 5
        DEC_TEST :X - 1
        """
        _, turtle = self.run_code(code)
        self.assertEqual(len(turtle.segments), 4 + 3)

    def test_output_reporter_procedures(self) -> None:
        code = """
        TO AREA :SIDE
            OUTPUT :SIDE * :SIDE
        END

        TO HYPOT :A :B
            OUTPUT SQRT (:A * :A + :B * :B)
        END

        FD AREA 5
        RT 90
        FD HYPOT 3 4
        """
        _, turtle = self.run_code(code)
        self.assertAlmostEqual(turtle.get_xcor(), 5.0, places=5)
        self.assertAlmostEqual(turtle.get_ycor(), 25.0, places=5)

    def test_make_thing_local_scoping(self) -> None:
        code = """
        MAKE "X 100
        TO SCOPE_TEST :A
            LOCAL "X
            MAKE "X :A + 5
            MAKE "LOCAL_READ THING "X
        END
        SCOPE_TEST 20
        """
        interp, _ = self.run_code(code)
        self.assertEqual(interp.global_env.get("X"), 100.0)
        self.assertEqual(interp.global_env.get("LOCAL_READ"), 25.0)

    # 2. Control Structures
    def test_control_primitives(self) -> None:
        code = """
        MAKE "ACC 0
        REPEAT 4 [MAKE "ACC :ACC + REPCOUNT]

        IF :ACC = 10 [MAKE "IF_OK 1]
        IFELSE :ACC > 20 [MAKE "BRANCH "HIGH] [MAKE "BRANCH "LOW]

        TEST :ACC = 10
        IFTRUE [MAKE "TEST_RES "PASSED]
        IFFALSE [MAKE "TEST_RES "FAILED]

        MAKE "FOR_SUM 0
        FOR [I 2 10 2] [MAKE "FOR_SUM :FOR_SUM + :I]

        MAKE "W 1
        WHILE [:W < 16] [MAKE "W :W * 2]

        MAKE "U 10
        UNTIL [:U = 0] [MAKE "U :U - 2]

        MAKE "FE 0
        FOREACH [10 20 30] [MAKE "FE :FE + ?]

        RUN [MAKE "RAN_OK 99]
        """
        interp, _ = self.run_code(code)
        self.assertEqual(interp.global_env.get("ACC"), 10.0)
        self.assertEqual(interp.global_env.get("IF_OK"), 1.0)
        self.assertEqual(interp.global_env.get("BRANCH"), "LOW")
        self.assertEqual(interp.global_env.get("TEST_RES"), "PASSED")
        self.assertEqual(interp.global_env.get("FOR_SUM"), 30.0)
        self.assertEqual(interp.global_env.get("W"), 16.0)
        self.assertEqual(interp.global_env.get("U"), 0.0)
        self.assertEqual(interp.global_env.get("FE"), 60.0)
        self.assertEqual(interp.global_env.get("RAN_OK"), 99.0)

    # 3. Math, Comparisons & Logic
    def test_math_and_logic_primitives(self) -> None:
        code = """
        MAKE "S (SUM 1 2 3 4 5)
        MAKE "D DIFFERENCE 20 7
        MAKE "P (PRODUCT 2 3 4)
        MAKE "Q QUOTIENT 22 4
        MAKE "REM REMAINDER -7 4
        MAKE "MOD MODULO -7 4
        MAKE "SQ SQRT 81
        MAKE "SN SIN 90
        MAKE "CS COS 0
        MAKE "AT ARCTAN 1
        MAKE "R1 RANDOM 100
        MAKE "R2 (RANDOM 50 60)
        MAKE "IN INT 3.9
        MAKE "RN ROUND 3.5
        MAKE "AB ABS -42.5
        MAKE "PW POWER 2 10
        MAKE "CMP1 (3 <= 3)
        MAKE "CMP2 (5 >= 6)
        MAKE "CMP3 (5 <> 6)
        MAKE "M_OP (17 % 5)
        MAKE "LG_AND (AND 1 (2 < 3) [4 = 4])
        MAKE "LG_OR (OR 0 (2 > 3) [10 = 10])
        MAKE "LG_NOT NOT 0
        """
        interp1, _ = self.run_code(code, seed=123)
        interp2, _ = self.run_code(code, seed=123)
        self.assertEqual(interp1.global_env.get("S"), 15.0)
        self.assertEqual(interp1.global_env.get("D"), 13.0)
        self.assertEqual(interp1.global_env.get("P"), 24.0)
        self.assertEqual(interp1.global_env.get("Q"), 5.5)
        self.assertEqual(interp1.global_env.get("REM"), -3.0)
        self.assertEqual(interp1.global_env.get("MOD"), 1.0)
        self.assertEqual(interp1.global_env.get("SQ"), 9.0)
        self.assertAlmostEqual(interp1.global_env.get("SN"), 1.0, places=6)
        self.assertAlmostEqual(interp1.global_env.get("CS"), 1.0, places=6)
        self.assertAlmostEqual(interp1.global_env.get("AT"), 45.0, places=6)
        # Reproducible seeded RANDOM
        self.assertEqual(interp1.global_env.get("R1"), interp2.global_env.get("R1"))
        self.assertTrue(50.0 <= interp1.global_env.get("R2") <= 60.0)
        self.assertEqual(interp1.global_env.get("IN"), 3.0)
        self.assertEqual(interp1.global_env.get("RN"), 4.0)
        self.assertEqual(interp1.global_env.get("AB"), 42.5)
        self.assertEqual(interp1.global_env.get("PW"), 1024.0)
        self.assertEqual(interp1.global_env.get("CMP1"), 1.0)
        self.assertEqual(interp1.global_env.get("CMP2"), 0.0)
        self.assertEqual(interp1.global_env.get("CMP3"), 1.0)
        self.assertEqual(interp1.global_env.get("M_OP"), 2.0)
        self.assertEqual(interp1.global_env.get("LG_AND"), 1.0)
        self.assertEqual(interp1.global_env.get("LG_OR"), 1.0)
        self.assertEqual(interp1.global_env.get("LG_NOT"), 1.0)

    # 4. Data Primitives (Lists & Words)
    def test_data_primitives(self) -> None:
        code = """
        MAKE "L (LIST 10 20 30)
        MAKE "S (SENTENCE [1 2] 3 [4 5])
        MAKE "W (WORD "HEL "LO "! )
        MAKE "F FIRST :S
        MAKE "LA LAST :S
        MAKE "BF BUTFIRST [A B C]
        MAKE "BL BUTLAST [A B C]
        MAKE "IT ITEM 3 :S
        MAKE "CNT COUNT :S
        MAKE "FP FPUT 0 :L
        MAKE "LP LPUT 40 :L
        MAKE "EMP1 EMPTYP []
        MAKE "EMP2 EMPTYP :L
        PRINT :W
        """
        interp, _ = self.run_code(code)
        self.assertEqual(interp.global_env.get("L"), LogoList.from_values([10.0, 20.0, 30.0]))
        self.assertEqual(interp.global_env.get("S"), LogoList.from_values([1.0, 2.0, 3.0, 4.0, 5.0]))
        self.assertEqual(interp.global_env.get("W"), "HELLO!")
        self.assertEqual(interp.global_env.get("F"), 1.0)
        self.assertEqual(interp.global_env.get("LA"), 5.0)
        self.assertEqual(interp.global_env.get("BF"), LogoList.from_values(["B", "C"]))
        self.assertEqual(interp.global_env.get("BL"), LogoList.from_values(["A", "B"]))
        self.assertEqual(interp.global_env.get("IT"), 3.0)
        self.assertEqual(interp.global_env.get("CNT"), 5.0)
        self.assertEqual(interp.global_env.get("FP"), LogoList.from_values([0.0, 10.0, 20.0, 30.0]))
        self.assertEqual(interp.global_env.get("LP"), LogoList.from_values([10.0, 20.0, 30.0, 40.0]))
        self.assertEqual(interp.global_env.get("EMP1"), 1.0)
        self.assertEqual(interp.global_env.get("EMP2"), 0.0)
        self.assertEqual(interp.output, ["HELLO!"])

    # 5. Turtle Tier 1 & Tier 2 Commands
    def test_turtle_commands_and_cs_vs_clean(self) -> None:
        code = """
        SETBG [240 240 250]
        SETPC 4 ; Red in MSWLogo palette
        SETPENSIZE 3
        FD 80
        RT 90
        FD 60
        CLEAN ; clears segments, keeps turtle at (60, 80) heading 90
        MAKE "X_AFTER_CLEAN XCOR
        MAKE "Y_AFTER_CLEAN YCOR
        MAKE "H_AFTER_CLEAN HEADING
        CS ; clears segments AND homes turtle to (0, 0) heading 0
        MAKE "POS_AFTER_CS POS
        MAKE "H_AFTER_CS HEADING

        SETX 50
        SETY -30
        PU
        HOME
        PD
        ARC 180 40
        ELLIPSE 30 15
        DOT
        FILLED "YELLOW [REPEAT 4 [FD 40 RT 90]]
        PE
        FD 10
        PX
        FD 20
        PPT
        ST
        LABEL "MSWLogo
        HT
        """
        interp, turtle = self.run_code(code)
        self.assertAlmostEqual(interp.global_env.get("X_AFTER_CLEAN"), 60.0, places=5)
        self.assertAlmostEqual(interp.global_env.get("Y_AFTER_CLEAN"), 80.0, places=5)
        self.assertAlmostEqual(interp.global_env.get("H_AFTER_CLEAN"), 90.0, places=5)
        self.assertEqual(interp.global_env.get("POS_AFTER_CS"), LogoList.from_values([0.0, 0.0]))
        self.assertEqual(interp.global_env.get("H_AFTER_CS"), 0.0)

        png_buf = turtle.render()
        img = Image.open(png_buf)
        self.assertEqual(img.size, (1000, 800))

        gif_buf = turtle.render_gif(max_frames=10, duration_ms=40)
        gif_img = Image.open(gif_buf)
        self.assertEqual(gif_img.format, "GIF")

    def test_multi_turtle_tell_and_ask(self) -> None:
        code = """
        TELL [0 1 2]
        FD 50
        ASK 1 [RT 90 FD 30]
        MAKE "ACTIVE WHO
        """
        interp, turtle = self.run_code(code)
        self.assertEqual(interp.global_env.get("ACTIVE"), LogoList.from_values([0.0, 1.0, 2.0]))
        self.assertEqual(len(turtle.segments), 4)

    def test_tail_call_optimization(self) -> None:
        # 500 tail-recursive calls succeed even though MAX_CALL_DEPTH is 100
        code = """
        TO SPIRAL :N
            IF :N <= 0 [STOP]
            FD 1
            RT 1
            SPIRAL :N - 1
        END
        SPIRAL 500
        """
        _, turtle = self.run_code(code)
        self.assertEqual(len(turtle.segments), 500)

    # 6. Abuse-Proofing & Hostile Fuzz Tests
    def test_hostile_color_validation(self) -> None:
        # "ACE" or "BED" must NOT match hex regex without # or 0x
        with self.assertRaises(LogoRuntimeError):
            parse_color("ACE")
        with self.assertRaises(LogoRuntimeError):
            parse_color("UNKNOWN_COLOR")
        with self.assertRaises(LogoRuntimeError):
            parse_color(99)  # palette index out of range 0..15
        self.assertEqual(parse_color("#ACE"), (0xAA, 0xCC, 0xEE))
        self.assertEqual(parse_color(LogoList.from_values([10, 20, 30])), (10, 20, 30))

    def test_hostile_giant_floats_and_overflow(self) -> None:
        # Giant fd clamp
        _, turtle = self.run_code("FD 1e300")
        png = turtle.render()
        self.assertGreater(len(png.getvalue()), 100)

        # Arithmetic overflow to inf raises LogoRuntimeError
        with self.assertRaises(LogoRuntimeError):
            self.run_code("FD 1e308 * 100")

    def test_hostile_infinite_recursion_and_loops(self) -> None:
        # Non-tail infinite recursion hits MAX_CALL_DEPTH
        with self.assertRaises(LogoRuntimeError):
            self.run_code("TO BOOM BOOM FD 1 END BOOM")

        # Tail infinite recursion hits MAX_OPERATIONS
        with self.assertRaises(LogoRuntimeError):
            self.run_code("TO TAIL_BOOM TAIL_BOOM END TAIL_BOOM")

        # Nested repeat bomb hits MAX_OPERATIONS
        with self.assertRaises(LogoRuntimeError):
            self.run_code("REPEAT 5000 [REPEAT 5000 [FD 1]]")

    def test_hostile_memory_and_structure_bombs(self) -> None:
        # Word doubling bomb stopped by MAX_WORD_LENGTH
        with self.assertRaises(LogoRuntimeError):
            self.run_code('MAKE "W "AAAA REPEAT 20 [MAKE "W WORD :W :W]')

        # List doubling bomb stopped by MAX_LIST_LENGTH
        with self.assertRaises(LogoRuntimeError):
            self.run_code('MAKE "L [1 2] REPEAT 20 [MAKE "L SENTENCE :L :L]')

        # Deep bracket nesting bomb stopped by MAX_NESTING_DEPTH
        deep_brackets = "[" * 60 + "FD 10" + "]" * 60
        with self.assertRaises(LogoSyntaxError):
            self.run_code(deep_brackets)

        # Oversized source length stopped by MAX_SOURCE_LENGTH
        huge_source = "FD 1\n" * 600
        with self.assertRaises(LogoSyntaxError):
            self.run_code(huge_source)

        # Single error type check: set_width raises LogoRuntimeError (subclass of LogoError)
        with self.assertRaises(LogoRuntimeError):
            self.run_code("SETWIDTH 999")



if __name__ == "__main__":
    unittest.main()

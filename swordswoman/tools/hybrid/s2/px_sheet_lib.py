"""shared helpers of px_sheet.py (my_body, retone_hair, corset_fix) without its CLI."""
import os
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "px_sheet.py")).read().split("\nap = argparse")[0]
__file__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "px_sheet.py")
exec(compile(_src, __file__, "exec"))

"""草稿/未知细节不再形成返回门槛，源素材路径与裁切结构仍须有效。"""
import importlib.util
from pathlib import Path
import sys
import unittest

PATH=Path(__file__).resolve().parents[1]/'scripts/build_boards.py'
spec=importlib.util.spec_from_file_location('car_boards_tested',PATH)
boards=importlib.util.module_from_spec(spec);sys.modules[spec.name]=boards;spec.loader.exec_module(boards)


class ReturnPolicyTests(unittest.TestCase):
    def test_legacy_status_does_not_gate_delivery(self):
        manifest={'views':[{'id':'L','status':'draft'}],'details':[{'id':'D1','critical':True,'side':'unknown','status':'uncertain','question':'旧确认问题','options':[]} ]}
        result=boards.readiness(manifest)
        self.assertTrue(result['ready']);self.assertEqual(result['returnChecks'],'skipped')
        self.assertEqual(result['reasons'],[]);self.assertEqual(result['pending_questions'],[])

    def test_empty_optional_details_and_views_can_still_be_laid_out(self):
        result=boards.readiness({'views':[],'details':[]})
        self.assertTrue(result['layoutReady']);self.assertTrue(result['missing_views'])


if __name__=='__main__':unittest.main()

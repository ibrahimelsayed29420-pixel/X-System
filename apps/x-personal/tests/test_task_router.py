import unittest

from x_personal.brain import system_prompt
from x_personal.real_estate import build_listing_draft
from x_personal.task_router import route_request


class TaskRouterTests(unittest.TestCase):
    def test_short_conversation_uses_local_dialogue_model(self):
        route = route_request('صباح الخير', 'x-ibrahim:latest', 'x-qwen-agent:latest')
        self.assertEqual(route['agent'], 'dialogue')
        self.assertEqual(route['model'], 'x-ibrahim:latest')

    def test_public_research_uses_research_specialist(self):
        route = route_request('ابحث عن أسعار الإيجارات في عجمان', 'x-ibrahim:latest', 'x-qwen-agent:latest')
        self.assertEqual(route['agent'], 'research-specialist')
        self.assertEqual(route['skill'], 'research')
        self.assertEqual(route['model'], 'x-qwen-agent:latest')

    def test_real_estate_work_uses_domain_specialist(self):
        route = route_request('صغ إعلانًا لهذه الشقة للإيجار', 'x-ibrahim:latest', 'x-qwen-agent:latest')
        self.assertEqual(route['agent'], 'real-estate-specialist')
        self.assertEqual(route['skill'], 'real_estate')
        self.assertEqual(route['model'], 'local-template')

    def test_listing_template_does_not_invent_missing_facts(self):
        draft = build_listing_draft(
            'اكتب مسودة إعلان لشقة للإيجار في عجمان. السعر والمساحة غير معروفة.'
        )
        self.assertIn('شقة للإيجار عجمان',draft)
        self.assertIn('السعر: [يُضاف بعد التأكيد]',draft)
        self.assertIn('التوافر: [يحتاج تأكيدًا من المالك]',draft)
        self.assertNotIn('متوفرة الآن',draft)
        self.assertNotIn('وسط المدينة',draft)

    def test_complex_request_uses_workflow_orchestrator(self):
        route = route_request('حلل وقارن الخيارات المتاحة', 'x-ibrahim:latest', 'x-qwen-agent:latest')
        self.assertEqual(route['agent'], 'workflow-orchestrator')
        self.assertEqual(route['skill'], 'planning')

    def test_explicit_plan_uses_planner_specialist(self):
        route = route_request('اكتب خطة من ثلاث خطوات', 'x-ibrahim:latest', 'x-qwen-agent:latest')
        self.assertEqual(route['agent'], 'workflow-planner')

    def test_disabled_agents_keep_direct_dialogue_route(self):
        route = route_request('ابحث عن معلومة حديثة', 'x-ibrahim:latest', 'x-qwen-agent:latest', False)
        self.assertEqual(route['agent'], 'research-specialist')
        self.assertEqual(route['model'], 'x-ibrahim:latest')

    def test_disabled_agents_do_not_start_planner(self):
        route = route_request('اكتب خطة من ثلاث خطوات', 'x-ibrahim:latest', 'x-qwen-agent:latest', False)
        self.assertEqual(route['agent'], 'dialogue')

    def test_empty_request_is_rejected(self):
        with self.assertRaises(ValueError):
            route_request(' ', 'x-ibrahim:latest', 'x-qwen-agent:latest')

    def test_real_estate_prompt_rejects_unverified_listing_facts(self):
        prompt = system_prompt('real_estate')
        self.assertIn('لا تخترع سعرًا',prompt)
        self.assertIn('لا تنشره',prompt)
        with self.assertRaises(ValueError):
            system_prompt('unknown')


if __name__ == '__main__':
    unittest.main()

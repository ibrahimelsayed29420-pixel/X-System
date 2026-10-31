import io
import unittest
import wave
from unittest.mock import patch

from mind_dashboard import Handler


def wav_payload(rate=16000,channels=1,width=2,frames=160):
    output=io.BytesIO()
    with wave.open(output,'wb') as audio:
        audio.setnchannels(channels)
        audio.setsampwidth(width)
        audio.setframerate(rate)
        audio.writeframes(bytes(frames*channels*width))
    return output.getvalue()


class MindDashboardChatTests(unittest.TestCase):
    def setUp(self):
        self.handler=object.__new__(Handler)

    def test_chat_calls_x_with_the_submitted_text(self):
        with patch('mind_dashboard.load_settings',return_value={'ollama_model':'x-ibrahim:latest'}), \
             patch('mind_dashboard.brain.answer',return_value='أهلًا') as answer:
            result=self.handler._chat({'text':'صباح الخير'})
        self.assertEqual(result,{'ok':True,'reply':'أهلًا'})
        answer.assert_called_once_with('صباح الخير','x-ibrahim:latest')

    def test_empty_or_overlong_chat_is_rejected(self):
        for text in ('  ','x'*4001):
            with self.subTest(length=len(text)),patch('mind_dashboard.brain.answer') as answer:
                with self.assertRaises(ValueError):
                    self.handler._chat({'text':text})
                answer.assert_not_called()

    def test_voice_is_transcribed_locally_after_identity_check(self):
        with patch('mind_dashboard.require_identity') as verify, \
             patch('mind_dashboard.load_settings',return_value={'speech_backend':'sherpa-onnx'}), \
             patch('x_personal.speech.ArabicListener') as listener_type:
            listener_type.return_value.transcribe.return_value='عايز أجهز إعلان عقاري'
            result=self.handler._transcribe(wav_payload())
        verify.assert_called_once()
        listener_type.return_value.transcribe.assert_called_once()
        self.assertEqual(result['text'],'عايز أجهز إعلان عقاري')

    def test_voice_rejects_noncanonical_audio_before_identity(self):
        with patch('mind_dashboard.require_identity') as verify:
            for payload in (wav_payload(rate=44100),wav_payload(channels=2),b'not a wave'):
                with self.subTest(payload=payload[:8]),self.assertRaises(ValueError):
                    self.handler._transcribe(payload)
        verify.assert_not_called()

    def test_voice_enforces_payload_size_before_transcription(self):
        with patch('mind_dashboard.require_identity') as verify:
            with self.assertRaises(ValueError):
                self.handler._transcribe(b'x'*4_000_001)
        verify.assert_not_called()


if __name__=='__main__':
    unittest.main()

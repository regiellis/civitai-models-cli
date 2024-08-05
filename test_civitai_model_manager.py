import os
import unittest
from unittest.mock import patch, MagicMock
import civitai_model_manager as manager
from rich.console import Console
from rich.table import Table

console = Console()

# TODO: Add more tests to cover all functions in civitai_model_manager.py
# TODO: Fix failing tests
class TestCivitaiModelManager(unittest.TestCase):

    @patch('os.walk')
    def test_list_models(self, mock_os_walk):
        """Test listing models in a directory."""
        mock_os_walk.return_value = [
            ('/fake_dir', ('subdir',), ('model1.safetensors', 'model2.ckpt')),
        ]
        expected_output = [
            ('model1', 'fake_dir', '/fake_dir/model1.safetensors'),
            ('model2', 'fake_dir', '/fake_dir/model2.ckpt'),
        ]
        self.assertEqual(manager.list_models('/fake_dir'), expected_output)

    @patch('os.walk')
    def test_count_models(self, mock_os_walk):
        """Test counting models in directories."""
        mock_os_walk.return_value = [
            ('/fake_dir/subdir1', (), ('model1.safetensors',)),
            ('/fake_dir/subdir2', (), ('model2.pt',)),
            ('/fake_dir/subdir3', (), ('model3.pth',)),
        ]
        expected_output = {
            'subdir1': 1,
            'subdir2': 1,
            'subdir3': 1,
        }
        self.assertEqual(manager.count_models('/fake_dir'), expected_output)

    @patch('os.path.getsize')
    @patch('os.walk')
    def test_get_model_sizes(self, mock_os_walk, mock_getsize):
        """Test getting model sizes in directories."""
        mock_os_walk.return_value = [
            ('/fake_dir', (), ('model1.safetensors', 'model2.pt')),
        ]
        mock_getsize.side_effect = [1048576, 2097152]  # 1 MB and 2 MB
        expected_output = {
            'model1.safetensors': '1.00 MB',
            'model2.pt': '2.00 MB',
        }
        self.assertEqual(manager.get_model_sizes('/fake_dir'), expected_output)
    
    @patch('civitai_model_manager.models.get_model')
    def test_get_model_details(self, mock_get_model):
        """Test getting model details by ID."""
        mock_model = MagicMock()
        mock_model.id = 12345
        mock_model.name = 'TestModel'
        mock_model.description = 'Model Description'
        mock_model.type = 'Checkpoint'
        
        version = MagicMock()
        version.id = 1
        version.name = 'v1'
        version.baseModel = 'BaseModel'
        version.files = [{'downloadUrl': 'url1'}]
        version.images = [{'url': 'img1'}]
        mock_model.modelVersions = [version]

        mock_model.tags = ['tag1', 'tag2']
        mock_get_model.return_value = mock_model
        
        expected_output = {
            'id': 12345,
            'name': 'TestModel',
            'description': 'Model Description',
            'type': 'Checkpoint',
            'versions': [{
                'id': 1,
                'name': 'v1',
                'base_model': 'BaseModel',
                'download_url': 'url1',
                'images': 'img1'
            }],
            'tags': ['tag1', 'tag2'],
        }
        self.assertEqual(manager.get_model_details(12345), expected_output)

    @patch('civitai_model_manager.requests.get')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_download_file(self, mock_open, mock_requests_get):
        """Test downloading a model file."""
        mock_response = MagicMock()
        content = [b'a' * 8192] * 10  # each chunk is 8192 bytes, 10 chunks total
        mock_response.iter_content = MagicMock(return_value=content)
        mock_response.headers = {'content-length': str(len(content) * 8192)}  # 81920 bytes total
        mock_requests_get.return_value = mock_response
        
        mock_file_handle = mock_open.return_value.__enter__.return_value
        mock_file_handle.write.side_effect = lambda x: len(x)  # Ensure write returns the size of written chunk

        model_path = manager.download_file('http://example.com/model', '/fake_dir/model.safetensors', 'Test Model')
        self.assertTrue(model_path)

    @patch('os.path.exists', return_value=True)  # Mock the file exists
    @patch('os.access', return_value=True)
    @patch('os.remove')
    @patch('builtins.input', return_value='y')
    @patch('civitai_model_manager.tqdm')
    def test_remove_model(self, mock_tqdm, mock_input, mock_os_remove, mock_os_access, mock_os_path_exists):
        """Test removing a model file."""
        mock_tqdm.return_value.__enter__.return_value.update = MagicMock()
        self.assertTrue(manager.remove_model('/fake_dir/model.safetensors'))  # Assert True since the file exists
        mock_os_remove.assert_called_once_with('/fake_dir/model.safetensors')  # Assert that os.remove is called with the correct path
        mock_tqdm.return_value.__enter__.return_value.update.assert_called_once()  # Assert that tqdm.update is called

    @patch('civitai_model_manager.get_model_details')
    @patch('civitai_model_manager.Ollama.chat')
    def test_summarize_model_description_ollama(self, mock_ollama_chat, mock_get_model_details):
        """Test summarizing model description using Ollama."""
        mock_get_model_details.return_value = {'description': 'Test description.'}
        mock_ollama_chat.return_value = {'message': {'content': 'Test summary'}}
        self.assertEqual(manager.summarize_model_description(12345, 'ollama'), 'Test summary')


class CustomTestResult(unittest.TextTestResult):
    results_list = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.results_list.append((test, "PASS", "green"))

    def addError(self, test, err):
        super().addError(test, err)
        self.results_list.append((test, f"ERROR: {err[1]}", "red"))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.results_list.append((test, f"FAIL: {err[1]}", "red"))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.results_list.append((test, f"SKIP: {reason}", "yellow"))

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.results_list.append((test, f"EXPECTED FAILURE: {err[1]}", "magenta"))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.results_list.append((test, "UNEXPECTED SUCCESS", "cyan"))


def print_results_to_table(results_list):
    table = Table(show_header=True, header_style="bold", title_justify="left")
    table.add_column("Test", style="dim", width=40)
    table.add_column("Description", width=60)
    table.add_column("Result")

    for result in results_list:
        test, message, color = result
        test_name = test.id().split('.')[-1]
        test_description = test.shortDescription() or ""
        table.add_row(test_name, test_description, f"[{color}]{message}[/{color}]")
    
    console.print(table)


if __name__ == '__main__':
    console.clear() # Clear the console before running tests
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCivitaiModelManager)
    runner = unittest.TextTestRunner(resultclass=CustomTestResult)
    result = runner.run(suite)
    print_results_to_table(result.results_list)
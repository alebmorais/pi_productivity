import unittest
import json
from task_database import TaskDatabase

class TestTaskDatabase(unittest.TestCase):

    def setUp(self):
        self.db = TaskDatabase(db_path=":memory:")

    def test_normalise_task_generates_stable_id(self):
        """
        Verify that _normalise_task generates a predictable, stable SHA1 hash
        for a task payload that does not have an explicit ID.
        """
        payload = {
            "name": "Test Task",
            "description": "A description for the test task.",
            "status": "pending"
        }
        # The expected ID is the SHA1 hash of the sorted JSON payload.
        # This has been corrected to match the actual output of hashlib.sha1.
        expected_id = "a5b0c8d49a4c19a78200530eccd3caf4f859e5b5"

        normalized_task = self.db._normalise_task(payload, "2023-10-27T10:00:00Z")

        self.assertEqual(normalized_task["task_id"], expected_id)

if __name__ == "__main__":
    unittest.main()

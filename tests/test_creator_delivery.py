import unittest

from src.creator_delivery import DeliveryItem, work_to_process


class DeliveryDecisionTest(unittest.TestCase):
    def test_processed_asset_is_skipped(self):
        item = DeliveryItem("asset-1", "subscriber-1", processed=True)
        self.assertFalse(work_to_process(item))

    def test_new_asset_enters_processing(self):
        item = DeliveryItem("asset-2", "subscriber-2", processed=False)
        self.assertTrue(work_to_process(item))


if __name__ == "__main__":
    unittest.main()

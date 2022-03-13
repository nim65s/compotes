"""Main test module."""

from decimal import Decimal
from random import randint

from django.db import models
from django.test import TestCase

from ndh.utils import query_sum

from .models import User, Debt, Part, Pool, Share


class CompotesTests(TestCase):
    """Main test class."""

    def setUp(self):
        """Create a few guys and their interractions for all tests."""
        for guy in "abcd":
            User.objects.create_user(guy, email=f"{guy}@example.org", password=guy)

    def test_models_debt(self):
        """Test 100.3€ debt between 4 users, CLI only."""
        creditor = User.objects.first()
        debt = Debt.objects.create(scribe=creditor, creditor=creditor, value=100.03)
        for user in User.objects.all():
            Part.objects.create(debt=debt, debitor=user, part=25)
        self.assertEqual(debt.part_value, 1.0003)
        self.assertEqual(Part.objects.first().value, 25.0075)
        self.assertEqual(User.objects.first().balance, Decimal("75.02"))
        self.assertEqual(User.objects.last().balance, Decimal("-25.01"))
        total = query_sum(
            User.objects.all(), "balance", output_field=models.DecimalField()
        )
        self.assertLess(total, Decimal("0.02"))
        self.assertGreater(total, Decimal("-0.02"))
        self.assertEqual(str(debt), "debt 1")
        self.assertEqual(debt.get_absolute_url(), "/debt/1")
        self.assertEqual(debt.get_edit_url(), "/debt/1/update")
        self.assertEqual(debt.get_parts_url(), "/debt/1/parts")
        self.assertEqual(debt.get_debitors(), 4)

    def test_models_pool(self):
        """Test 100€ pool for 4 users ready to give 30€ each, CLI only."""
        organiser = User.objects.first()
        pool = Pool.objects.create(
            name="smth", organiser=organiser, description="smth", value=100
        )
        for user in User.objects.all():
            Share.objects.create(pool=pool, participant=user, maxi=30)
        self.assertEqual(pool.ratio, 1 / 1.2)
        self.assertEqual(Share.objects.first().value, 25)
        self.assertEqual(User.objects.first().balance, 75)
        self.assertEqual(User.objects.last().balance, -25)
        self.assertEqual(
            query_sum(
                User.objects.all(), "balance", output_field=models.DecimalField()
            ),
            0,
        )
        self.assertEqual(pool.get_absolute_url(), "/pool/smth")
        self.assertEqual(pool.get_edit_url(), "/pool/smth/update")
        self.assertEqual(pool.get_share_url(), "/pool/smth/share")
        self.assertEqual(
            pool.share_set.first().get_absolute_url(), pool.get_absolute_url()
        )

    def test_multiple_parts_per_user(self):
        """Test 109€ debt for 20x4 users, with one of those users having another 29."""
        creditor = User.objects.first()
        debt = Debt.objects.create(scribe=creditor, creditor=creditor, value=109)
        for user in User.objects.all():
            Part.objects.create(debt=debt, debitor=user, part=20, description="first")
        Part.objects.create(debt=debt, debitor=user, part=29, description="second")
        self.assertEqual(debt.part_value, 1)

    def test_rand(self):
        """Generate random data, check balances."""
        user = User.objects.first()
        for _ in range(randint(2, 10)):
            value = randint(2000, 10000) / 100
            debt = Debt.objects.create(scribe=user, creditor=user, value=value)
            for user in User.objects.all():
                Part.objects.create(debt=debt, debitor=user, part=randint(0, 5))
        for i in range(randint(2, 10)):
            value = randint(1000, 20000) / 100
            pool = Pool.objects.create(
                name=f"rand_{i}", organiser=user, description="rand", value=value
            )
            for user in User.objects.all():
                Share.objects.create(pool=pool, participant=user, maxi=randint(10, 50))
        total = query_sum(
            User.objects.all(), "balance", output_field=models.DecimalField()
        )
        self.assertLess(total, Decimal("0.02"))
        self.assertGreater(total, Decimal("-0.02"))

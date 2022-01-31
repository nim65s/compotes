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

    def test_models_debt_100_3(self):
        """Test 100.3€ debt between 4 users, CLI only."""
        creditor = User.objects.first()
        debt = Debt.objects.create(
            scribe=creditor, creditor=creditor, value=100.03, draft=False
        )
        for user in User.objects.all():
            Part.objects.create(debt=debt, debitor=user, part=25)
        debt.update()
        self.assertEqual(debt.part_value, 1.0003)
        self.assertEqual(Part.objects.first().value, 25.0075)
        self.assertEqual(User.objects.first().balance, Decimal("75.02"))
        self.assertEqual(User.objects.last().balance, Decimal("-25.01"))
        total = query_sum(
            User.objects.all(), "balance", output_field=models.DecimalField()
        )
        self.assertLess(total, Decimal("0.02"))
        self.assertGreater(total, Decimal("-0.02"))

    def test_models_pool_100(self):
        """Test 100€ pool for 4 users ready to give 30€ each, CLI only."""
        organiser = User.objects.first()
        pool = Pool.objects.create(
            name="smth", organiser=organiser, description="smth", value=100
        )
        for user in User.objects.all():
            Share.objects.create(pool=pool, participant=user, maxi=30)
        pool.update()
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

    def test_rand(self):
        """Generate random data, check balances."""
        user = User.objects.first()
        for _ in range(randint(2, 10)):
            value = randint(2000, 10000) / 100
            debt = Debt.objects.create(scribe=user, creditor=user, value=value)
            for user in User.objects.all():
                Part.objects.create(debt=debt, debitor=user, part=randint(0, 5))
            debt.update()
        for i in range(randint(2, 10)):
            value = randint(1000, 20000) / 100
            pool = Pool.objects.create(
                name=f"rand_{i}", organiser=user, description="rand", value=value
            )
            for user in User.objects.all():
                Share.objects.create(pool=pool, participant=user, maxi=randint(10, 50))
            pool.update()
        total = query_sum(
            User.objects.all(), "balance", output_field=models.DecimalField()
        )
        self.assertLess(total, Decimal("0.02"))
        self.assertGreater(total, Decimal("-0.02"))

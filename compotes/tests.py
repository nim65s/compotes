"""Main test module."""

from decimal import Decimal
from random import randint

from django.core import mail
from django.core.management import call_command
from django.db import models
from django.test import TestCase
from django.urls import reverse

from ndh.utils import query_sum

from actions.models import Action

from .models import Debt, Part, Pool, Share, User


class CompotesTests(TestCase):
    """Main test class."""

    def setUp(self):
        """Create a few guys and their interractions for all tests."""
        for guy in "abcd":
            User.objects.create_user(guy, email=f"{guy}@example.org", password=guy)

    def test_models_user(self):
        """Detail."""
        user = User.objects.first()
        self.assertEqual(user.get_absolute_url(), "/user/a")
        self.assertEqual(repr(user), "a")
        user.first_name = "Joe"
        user.last_name = "Dohn"
        user.save()
        self.assertEqual(repr(User.objects.first()), "Joe Dohn (a)")
        user.first_name = "Jane"
        user.save()
        self.assertEqual(repr(User.objects.first()), "Jane Dohn")

    def test_models_debt(self):
        """Test 100.3 € debt between 4 users, CLI only."""
        creditor = User.objects.first()
        debt = Debt.objects.create(creditor=creditor, value=100.03, name="debt 1")
        for user in User.objects.all():
            Part.objects.create(debt=debt, debitor=user, part=25)
        self.assertEqual(debt.part_value, 1.0003)
        self.assertEqual(Part.objects.first().value, 25.0075)
        self.assertEqual(User.objects.first().balance, Decimal("75.02"))
        self.assertEqual(User.objects.last().balance, Decimal("-25.01"))
        total = query_sum(
            User.objects.all(),
            "balance",
            output_field=models.DecimalField(),
        )
        self.assertLess(total, Decimal("0.02"))
        self.assertGreater(total, Decimal("-0.02"))
        self.assertEqual(str(debt), "debt 1")
        self.assertEqual(debt.get_absolute_url(), "/debt/1")
        self.assertEqual(debt.get_edit_url(), "/debt/1/update")
        self.assertEqual(debt.get_debitors(), 4)
        self.assertEqual(
            str(Part.objects.first()),
            "Part of 25.01 € from a for debt 1: ",
        )

    def test_models_pool(self):
        """Test 100 € pool for 4 users ready to give 30 € each, CLI only."""
        organiser = User.objects.first()
        pool = Pool.objects.create(
            name="smth",
            organiser=organiser,
            description="smth",
            value=100,
        )
        for user in User.objects.all():
            Share.objects.create(pool=pool, participant=user, maxi=30)
        self.assertEqual(pool.ratio, 1 / 1.2)
        self.assertEqual(Share.objects.first().value, 25)
        self.assertEqual(User.objects.first().balance, 75)
        self.assertEqual(User.objects.last().balance, -25)
        self.assertEqual(
            query_sum(
                User.objects.all(),
                "balance",
                output_field=models.DecimalField(),
            ),
            0,
        )
        self.assertEqual(pool.get_absolute_url(), "/pool/smth")
        self.assertEqual(pool.get_edit_url(), "/pool/smth/update")
        self.assertEqual(pool.get_share_url(), "/pool/smth/share")
        self.assertEqual(
            pool.share_set.first().get_absolute_url(),
            pool.get_absolute_url(),
        )
        self.assertEqual(
            str(Share.objects.first()),
            "Share of 25.0 / 30.00 from a for smth",
        )
        self.assertEqual(pool.real_shares().count(), 4)
        self.assertEqual(pool.missing(), -20)

    def test_multiple_parts_per_user(self):
        """Test 109 € debt for 20x4 users, with one of those users having another 29."""
        creditor = User.objects.first()
        debt = Debt.objects.create(creditor=creditor, value=109)
        for user in User.objects.all():
            Part.objects.create(debt=debt, debitor=user, part=20, description="first")
        Part.objects.create(debt=debt, debitor=user, part=29, description="second")
        self.assertEqual(debt.part_value, 1)
        self.assertEqual(debt.get_debitors(), 4)
        self.assertEqual(debt.get_parts(), 109)

    def test_rand(self):
        """Generate random data, check balances."""
        user = User.objects.first()
        for _ in range(randint(2, 10)):
            value = randint(2000, 10000) / 100
            debt = Debt.objects.create(creditor=user, value=value)
            for user in User.objects.all():
                Part.objects.create(debt=debt, debitor=user, part=randint(0, 5))
        for i in range(randint(2, 10)):
            value = randint(1000, 20000) / 100
            pool = Pool.objects.create(
                name=f"rand_{i}",
                organiser=user,
                description="rand",
                value=value,
            )
            for user in User.objects.all():
                Share.objects.create(pool=pool, participant=user, maxi=randint(10, 50))
        total = query_sum(
            User.objects.all(),
            "balance",
            output_field=models.DecimalField(),
        )
        self.assertLess(total, Decimal("0.02"))
        self.assertGreater(total, Decimal("-0.02"))

    def test_debt_views_mails(self):
        """Check debt views."""
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Action.objects.count(), 0)

        # Client not logged in
        r = self.client.get(reverse("debt_create"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("accounts/login", r.url)

        # Create Debt
        self.client.login(username="a", password="a")
        r = self.client.get(reverse("debt_create"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Debt.objects.count(), 0)
        debt = {
            "name": "test",
            "creditor": 1,
            "description": "test",
            "value": 30,
            "date_0": "2022-08-29",
            "date_1": "23:33:30",
        }
        r = self.client.post(reverse("debt_create"), debt)
        self.assertEqual(Debt.objects.count(), 1)
        self.assertEqual(Action.objects.count(), 1)
        debt = Debt.objects.first()

        # No balance change → no mails
        self.assertEqual(len(mail.outbox), 0)

        # Add a part
        part = {"debitor": "1", "part": "2", "description": "test"}
        r = self.client.post(reverse("part_create", kwargs={"pk": debt.pk}), part)
        self.assertEqual(Part.objects.count(), 1)
        self.assertEqual(Action.objects.count(), 2)
        inst = Part.objects.first()

        # Update it
        part["part"] = "3"
        r = self.client.post(reverse("part_update", kwargs={"pk": inst.pk}), part)
        self.assertEqual(Action.objects.count(), 3)

        # Delete it
        r = self.client.post(reverse("part_delete", kwargs={"pk": inst.pk}))
        self.assertEqual(Part.objects.count(), 0)
        self.assertEqual(Action.objects.count(), 4)
        self.assertEqual(
            Action.objects.last().item(),
            {
                "model": "compotes.part",
                "pk": None,
                "fields": {
                    "debt": 1,
                    "debitor": 1,
                    "part": 3.0,
                    "value": 30.0,
                    "description": "test",
                },
            },
        )

        # Get list
        self.client.get(reverse("debt_detail", kwargs={"pk": debt.pk}))

    def test_pool_views_mails(self):
        """Check pool views."""
        self.assertEqual(len(mail.outbox), 0)

        # Client not logged in
        r = self.client.get(reverse("pool_create"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("accounts/login", r.url)

        # Create Pool
        self.client.login(username="a", password="a")
        r = self.client.get(reverse("pool_create"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Pool.objects.count(), 0)
        pool = {"name": "z", "description": "test", "value": 60}
        r = self.client.post(reverse("pool_create"), pool)
        self.assertEqual(Pool.objects.count(), 1)

        # No balance change → no mails
        self.assertEqual(len(mail.outbox), 0)

        # Add shares
        self.assertEqual(Share.objects.count(), 0)
        url = reverse("share_update", kwargs={"slug": "z"})
        r = self.client.post(url, {"maxi": 10})
        self.client.login(username="b", password="b")
        r = self.client.post(url, {"maxi": 20})
        self.client.login(username="c", password="c")
        r = self.client.post(url, {"maxi": 30})
        self.assertEqual(Share.objects.count(), 3)

        # Get Pool Detail view
        self.client.get(reverse("pool_detail", kwargs={"slug": "z"}))

    def test_views(self):
        """Check missing views."""
        # Check an user can update another's debt
        debt = {
            "name": "test",
            "creditor": 1,
            "description": "test",
            "value": 30,
            "date_0": "2022-08-29",
            "date_1": "23:33:30",
        }
        self.client.login(username="a", password="a")  # they can
        self.client.post(reverse("debt_create"), debt)
        self.assertEqual(Debt.objects.first().value, 30)
        debt["value"] = 50
        r = self.client.post(reverse("debt_update", kwargs={"pk": 1}), debt)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, "/debt/1")
        self.assertEqual(Debt.objects.first().value, 50)
        self.client.login(username="b", password="b")  # they can't
        debt["value"] = 40
        r = self.client.post(reverse("debt_update", kwargs={"pk": 1}), debt)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Debt.objects.first().value, 40)

        # Check an user can update another's pool
        pool = {"name": "z", "description": "test", "value": 30}
        self.client.login(username="a", password="a")  # they can
        self.client.post(reverse("pool_create"), pool)
        self.assertEqual(Pool.objects.first().value, 30)
        pool["value"] = 50
        r = self.client.post(reverse("pool_update", kwargs={"slug": "z"}), pool)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, "/pool/z")
        self.assertEqual(Pool.objects.first().value, 50)
        self.client.login(username="b", password="b")  # they can't
        pool["value"] = 40
        r = self.client.post(reverse("pool_update", kwargs={"slug": "z"}), pool)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Pool.objects.first().value, 40)

        # Ensure this created the right Actions
        self.assertEqual(Action.objects.count(), 6)
        self.assertEqual(str(Action.objects.first()), "a created test")
        self.assertEqual(str(Action.objects.last()), "b updated z")

        # Check user table
        self.client.get(reverse("home"))

        # Check debt table
        self.client.get(reverse("debt_list"))
        self.client.get(reverse("debt_list"), data={"user": "a"})
        self.client.get(reverse("debt_list"), data={"debt": "test"})

        # Check debt detail
        self.client.get(reverse("debt_detail", kwargs={"pk": 1}))

        # Check user detail
        self.client.get(reverse("user_detail", kwargs={"slug": "a"}))

    def test_pool_list(self):
        """Check an user can see the Pool they create, share, but nothing more."""
        a, b, c, d = User.objects.all()
        z = Pool.objects.create(name="z", organiser=a, description="z", value=100)
        y = Pool.objects.create(name="y", organiser=b, description="y", value=100)
        Share.objects.create(pool=z, participant=a, maxi=50)
        Share.objects.create(pool=z, participant=b, maxi=50)
        Share.objects.create(pool=z, participant=c, maxi=50)
        Share.objects.create(pool=y, participant=a, maxi=50)
        Share.objects.create(pool=y, participant=d, maxi=50)
        self.client.login(username="a", password="a")
        page = self.client.get(reverse("pool_list")).content.decode()
        self.assertIn("pool/z", page)
        self.assertIn("pool/y", page)
        self.client.login(username="b", password="b")
        page = self.client.get(reverse("pool_list")).content.decode()
        self.assertIn("pool/z", page)
        self.assertIn("pool/y", page)
        self.client.login(username="c", password="c")
        page = self.client.get(reverse("pool_list")).content.decode()
        self.assertIn("pool/z", page)
        self.assertNotIn("pool/y", page)
        self.client.login(username="d", password="d")
        page = self.client.get(reverse("pool_list")).content.decode()
        self.assertNotIn("pool/z", page)
        self.assertIn("pool/y", page)

    def test_reminder(self):
        """Run the "reminder" management command."""
        # Get some data
        a, b, c, d = User.objects.all()
        z = Pool.objects.create(name="z", organiser=a, description="z", value=100)
        y = Pool.objects.create(name="y", organiser=b, description="y", value=100)
        Share.objects.create(pool=z, participant=a, maxi=50)
        Share.objects.create(pool=z, participant=b, maxi=50)
        Share.objects.create(pool=z, participant=c, maxi=50)
        Share.objects.create(pool=y, participant=a, maxi=50)
        Share.objects.create(pool=y, participant=d, maxi=50)

        # Call the command
        mail.outbox = []
        call_command("reminder")
        self.assertEqual(len(mail.outbox), 4)
        self.assertIn("Hi a", mail.outbox[0].body)
        self.assertIn("is 16.67 €", mail.outbox[0].body)
        self.assertIn("Hi b", mail.outbox[1].body)
        self.assertIn("is 66.67 €", mail.outbox[1].body)
        self.assertIn("Hi c", mail.outbox[2].body)
        self.assertIn("is -33.33 €", mail.outbox[2].body)
        self.assertIn("Hi d", mail.outbox[3].body)
        self.assertIn("is -50.00 €", mail.outbox[3].body)

        # d gives 50 € to b
        debt = Debt.objects.create(creditor=d, value=50)
        Part.objects.create(debt=debt, debitor=b, part=1)

        # Call the command
        mail.outbox = []
        call_command("reminder")
        self.assertEqual(len(mail.outbox), 3)
        self.assertIn("Hi a", mail.outbox[0].body)
        self.assertIn("is 16.67 €", mail.outbox[0].body)
        self.assertIn("Hi b", mail.outbox[1].body)
        self.assertIn("is 16.67 €", mail.outbox[1].body)
        self.assertIn("Hi c", mail.outbox[2].body)
        self.assertIn("is -33.33 €", mail.outbox[2].body)

    def test_pool_table(self):
        """Check Pool table has the right row colors."""
        a, b, c, d = User.objects.all()

        # z is a successful Pool
        z = Pool.objects.create(name="z", organiser=a, description="z", value=100)
        Share.objects.create(pool=z, participant=a, maxi=40)
        Share.objects.create(pool=z, participant=b, maxi=40)
        Share.objects.create(pool=z, participant=c, maxi=40)
        self.client.login(username="a", password="a")
        data = self.client.get(reverse("pool_list")).content.decode()
        self.assertNotIn("table-warning", data)

        # y isn't
        y = Pool.objects.create(name="y", organiser=b, description="y", value=100)
        Share.objects.create(pool=y, participant=a, maxi=40)
        Share.objects.create(pool=y, participant=d, maxi=40)
        data = self.client.get(reverse("pool_list")).content.decode()
        self.assertIn("table-warning", data)

    def test_delete_debitor(self):
        """Check user balances are updated on delete."""
        a, b, *_ = User.objects.all()

        # Create Debt
        self.client.login(username="a", password="a")
        r = self.client.get(reverse("debt_create"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Debt.objects.count(), 0)
        debt = {
            "name": "test",
            "creditor": 1,
            "description": "test",
            "value": 30,
            "date_0": "2022-08-29",
            "date_1": "23:33:30",
        }
        r = self.client.post(reverse("debt_create"), debt)
        self.assertEqual(Debt.objects.count(), 1)
        self.assertEqual(Action.objects.count(), 1)
        debt = Debt.objects.first()

        # Add a part
        part = {"debitor": "2", "part": "2", "description": "test"}
        r = self.client.post(reverse("part_create", kwargs={"pk": debt.pk}), part)
        self.assertEqual(Part.objects.count(), 1)
        self.assertEqual(Action.objects.count(), 2)
        part = Part.objects.first()

        # Check b balance
        a, b, *_ = User.objects.all()
        self.assertEqual(a.balance, 30)
        self.assertEqual(b.balance, -30)

        # Remove the part
        r = self.client.post(reverse("part_delete", kwargs={"pk": part.pk}))
        self.assertEqual(Part.objects.count(), 0)
        self.assertEqual(Action.objects.count(), 3)

        # Check b balance
        a, b, *_ = User.objects.all()
        self.assertEqual(a.balance, 0)
        self.assertEqual(b.balance, 0)

"""
Management command to seed 1 floor × 38 rooms = 38 rooms total.

Usage:
    python manage.py seed_rooms
"""
from django.core.management.base import BaseCommand
from hostelmgmt.models import Hostel, Block, Floor, Room


class Command(BaseCommand):
    help = 'Seed hostel with 1 floor × 38 rooms (38 rooms total, capacity 2 each)'

    def handle(self, *args, **kwargs):
        # Create Hostel
        hostel, created = Hostel.objects.get_or_create(
            hostel_code='H001',
            defaults={
                'hostel_name': 'PRAVAAH Main Hostel',
                'address': 'PRAVAAH Campus, Main Road',
                'status': 'active',
            }
        )
        if created:
            self.stdout.write(f'  ✅ Created hostel: {hostel.hostel_name}')
        else:
            self.stdout.write(f'  ℹ️  Hostel already exists: {hostel.hostel_name}')

        # Create Block
        block, created = Block.objects.get_or_create(
            hostel=hostel,
            block_name='Block A',
        )
        if created:
            self.stdout.write(f'  ✅ Created block: {block.block_name}')

        # Create single floor
        floor, _ = Floor.objects.get_or_create(
            block=block,
            floor_no=1,
        )

        room_count = 0
        # Create 38 rooms: numbered 1 to 38
        for room_no in range(1, 39):
            room_number = str(room_no)
            room, created = Room.objects.get_or_create(
                floor=floor,
                room_number=room_number,
                defaults={
                    'capacity': 2,
                    'occupied': 0,
                    'status': 'available',
                    'gender': None,
                }
            )
            if created:
                room_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🏨 Done! {room_count} new rooms created on Floor 1.\n'
                f'   Total rooms in DB: {Room.objects.count()}'
            )
        )
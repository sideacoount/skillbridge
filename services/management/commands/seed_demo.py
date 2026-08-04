from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone
from PIL import Image, ImageDraw

from accounts.models import User, Notification
from bookings.models import Booking
from reviews.models import Review
from services.models import Category, Service

CATEGORIES = [
    ('Graphic Design', 'bi-palette', 'Logos, branding, posters and everything visual'),
    ('Web Development', 'bi-code-slash', 'Websites and web apps built to last'),
    ('UI/UX', 'bi-layers', 'Interfaces and experiences users love'),
    ('Photography', 'bi-camera', 'Portraits, products and event photography'),
    ('Programming', 'bi-terminal', 'Scripts, tools and software solutions'),
    ('Typing', 'bi-keyboard', 'Fast, accurate transcription and data entry'),
    ('Video Editing', 'bi-film', 'Edits, motion graphics and YouTube-ready videos'),
    ('Tutoring', 'bi-mortarboard', 'One-on-one help in any subject'),
    ('Writing', 'bi-pencil', 'Articles, copy and storytelling that converts'),
    ('Animation', 'bi-play-circle', '2D/3D animations and explainer videos'),
    ('Marketing', 'bi-megaphone', 'Social media, SEO and growth strategy'),
    ('Data Analysis', 'bi-bar-chart', 'Spreadsheets, dashboards and insights'),
    ('Others', 'bi-box', 'Anything else you do brilliantly'),
]

SERVICES = [
    ('Modern logo & brand kit', 'Web Development', 49, 'A complete brand identity: primary logo, icon, color palette and usage guidelines in 3 business days. Two revision rounds included.', 'Graphic Design'),
    ('Landing page in 48h', 'Web Development', 120, 'High-converting, responsive landing page built with HTML, CSS and JavaScript. Mobile-first, SEO-friendly, deploys to your host.', 'Web Development'),
    ('Mobile app UI design', 'UI/UX', 180, 'Pixel-perfect Figma screens for iOS and Android, with a design system and interactive prototype you can hand to any developer.', 'UI/UX'),
    ('Product photography pack', 'Photography', 85, '10 edited studio-style product photos with clean backgrounds, ready for your store or social media.', 'Photography'),
    ('Python automation scripts', 'Programming', 95, 'Custom Python scripts to scrape data, automate reports or clean messy files. Delivered with readable, commented code.', 'Programming'),
    ('YouTube video editing', 'Video Editing', 75, 'Full editing with captions, b-roll, sound design and motion text. 5–15 minute videos delivered in 2 days.', 'Video Editing'),
    ('Math & physics tutoring', 'Tutoring', 25, 'Weekly one-on-one sessions online, including homework help and exam prep. Available evenings and weekends.', 'Tutoring'),
    ('SEO blog articles', 'Writing', 60, 'Research-backed, search-optimized articles (800–1500 words) written in your brand voice with meta descriptions included.', 'Writing'),
    ('Explainer animation 30s', 'Animation', 140, '2D motion graphics explainer with voiceover sync and brand colors. Perfect for product launches and pitch decks.', 'Animation'),
    ('Social media growth plan', 'Marketing', 90, '30-day content calendar, posting schedule and copy for three platforms. Includes monthly analytics review.', 'Marketing'),
    ('Excel dashboard & analytics', 'Data Analysis', 110, 'Automated Excel/Google Sheets dashboard with formulas, pivots and charts that update with your data.', 'Data Analysis'),
    ('Typed transcription service', 'Typing', 35, 'Accurate transcription of audio/video up to 60 minutes, 98%+ accuracy, delivered in 24 hours.', 'Typing'),
    ('E-commerce website build', 'Web Development', 300, 'Full storefront with product pages, cart and checkout integration. Based on Django and Stripe-ready for real payments.', 'Web Development'),
    ('Instagram content pack', 'Marketing', 55, '10 designed posts + 10 story templates + captions and hashtags for two weeks of consistent posting.', 'Graphic Design'),
]

BIO = ('Student developer with a passion for clean, modern products. '
       'I’ve shipped projects for startups, local businesses and classmates — '
       'always on time, always friendly. Let’s build something great together!')

OCCUPATIONS = ['Freelance Web Developer', 'UI/UX Design Student', 'Video Editor',
               'Data Science Student', 'Graphic Designer', 'Marketing Assistant',
               'Photographer', 'Programming Tutor']


class Command(BaseCommand):
    help = 'Seed SkillBridge with categories, demo users, services, bookings and reviews.'

    def handle(self, *args, **options):
        self.create_categories()
        admin = self.create_admin()
        providers = self.create_providers()
        clients = self.create_clients()
        services = self.create_services(providers)
        self.create_bookings_and_reviews(providers, clients, services)
        self.stdout.write(self.style.SUCCESS('Seed complete. Enjoy SkillBridge!'))
        self.stdout.write(f'  Admin:     {admin.username} / admin123')
        for i, p in enumerate(providers[:2]):
            self.stdout.write(f'  Provider:  {p.username} / student{i+1}123')
        self.stdout.write(f'  Client:    {clients[0].username} / client123')

    def create_categories(self):
        for name, icon, desc in CATEGORIES:
            Category.objects.get_or_create(
                name=name, defaults={'icon': icon, 'description': desc},
            )
        self.stdout.write(f'  Categories: {Category.objects.count()}')

    def create_admin(self):
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@skillbridge.app', 'is_staff': True, 'is_superuser': True},
        )
        if created:
            admin.set_password('admin123')
            admin.first_name = 'Bridge'
            admin.last_name = 'Admin'
            admin.role = User.Role.CLIENT
            admin.save()
            self.stdout.write('  Admin created')
        return admin

    def create_providers(self):
        names = [
            ('amina', 'Amina', 'Khalid', 'UI/UX Design Student'),
            ('james', 'James', 'Mwangi', 'Full-stack Developer'),
            ('sophia', 'Sophia', 'Nguyen', 'Graphic Designer'),
            ('liam', 'Liam', 'O''Brien', 'Video Editor'),
            ('fatima', 'Fatima', 'Hassan', 'Data Science Student'),
            ('diego', 'Diego', 'Ramirez', 'Photography Student'),
        ]
        providers = []
        for i, (uname, first, last, occ) in enumerate(names, start=1):
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f'{uname}@skillbridge.app',
                    'first_name': first, 'last_name': last,
                    'role': User.Role.STUDENT,
                    'is_provider_approved': True,
                    'occupation': occ,
                    'location': ['Nairobi, Kenya', 'Hanoi, Vietnam', 'Lagos, Nigeria',
                                 'São Paulo, Brazil', 'Manila, Philippines', 'Mexico City, Mexico'][i - 1],
                    'phone': f'+254 700 0000{i}',
                    'bio': BIO,
                },
            )
            if created:
                user.set_password(f'student{i}123')
                user.save()
            user.skills.set(Category.objects.all().order_by('?')[:3])
            self.make_avatar(user, i)
            providers.append(user)
        return providers

    def create_clients(self):
        names = [('sarah', 'Sarah', 'Mitchell'), ('david', 'David', 'Chen')]
        clients = []
        for i, (uname, first, last) in enumerate(names, start=1):
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f'{uname}@example.com', 'first_name': first, 'last_name': last,
                    'role': User.Role.CLIENT, 'occupation': 'Startup founder',
                    'location': 'Remote', 'bio': 'Hiring students to do great work, fast.',
                },
            )
            if created:
                user.set_password('client123')
                user.save()
            clients.append(user)
        return clients

    def create_services(self, providers):
        cats = {c.name: c for c in Category.objects.all()}
        services = []
        # Spread services across providers with the correct categories
        for i, (title, cat_name, price, desc, _) in enumerate(SERVICES):
            provider = providers[i % len(providers)]
            service, created = Service.objects.get_or_create(
                provider=provider, title=title,
                defaults={
                    'category': cats[cat_name],
                    'description': desc,
                    'price': price,
                    'availability': 'available',
                },
            )
            if created:
                service.image.save(f'service_{i}.png', self.make_image(title), save=True)
            services.append(service)
        # a couple of extra services so some providers have multiple
        extra = Service.objects.create(
            provider=providers[1], category=cats['Web Development'],
            title='Django REST API development', description='RESTful APIs with auth, docs and tests.',
            price=220, availability='limited',
        )
        extra.image.save('service_api.png', self.make_image('Django REST API'), save=True)
        services.append(extra)
        return services

    def create_bookings_and_reviews(self, providers, clients, services):
        statuses = ['completed', 'completed', 'accepted', 'pending', 'completed', 'cancelled']
        for i, service in enumerate(services[:6]):
            client = clients[i % len(clients)]
            booking, created = Booking.objects.get_or_create(
                client=client, provider=service.provider, service=service,
                defaults={
                    'status': statuses[i],
                    'preferred_date': (timezone.now() + timezone.timedelta(days=i + 2)).date(),
                    'budget': service.price + 20,
                    'description': 'Looking for a fast turnaround on this — happy to hop on a quick call first.',
                },
            )
            if created and booking.status == 'completed':
                Review.objects.get_or_create(
                    client=client, provider=service.provider,
                    defaults={
                        'service': service,
                        'rating': 4 if i % 2 else 5,
                        'comment': ('Flawless work, delivered early. Highly recommended!' if i % 2 == 0
                                    else 'Really solid quality. A few small revisions needed but the result was great.'),
                    },
                )
                Notification.objects.create(
                    user=service.provider, title='New review',
                    message=f'{client.username} left you a review.',
                )

        # Seed notifications for a lively dashboard
        Notification.objects.get_or_create(
            user=providers[0], title='New booking request',
            defaults={'message': 'Sarah Mitchell booked “Landing page in 48h”.',
                      'link': f'/bookings/{Booking.objects.filter(service=services[1]).first().pk}/'},
        )

    # ---- helpers ----
    def make_image(self, title):
        """Generate a branded gradient placeholder image."""
        width, height = 800, 500
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        top = (37, 99, 235)
        bottom = (6, 182, 212)
        for y in range(height):
            t = y / height
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        draw.ellipse([width - 260, -80, width + 120, 300], fill=(255, 255, 255, 18))
        draw.ellipse([-120, height - 220, 220, height + 100], fill=(255, 255, 255, 12))
        draw.text((60, height - 90), title[:44], fill=(255, 255, 255, 255))
        buf = BytesIO()
        img.save(buf, format='PNG')
        return ContentFile(buf.getvalue())

    def make_avatar(self, user, seed):
        """Generate a simple gradient avatar based on a seed number."""
        if user.profile_image:
            return
        colors = [(37, 99, 235), (6, 182, 212), (16, 185, 129),
                  (139, 92, 246), (245, 158, 11), (239, 68, 68)]
        c = colors[(seed - 1) % len(colors)]
        img = Image.new('RGB', (256, 256), c)
        draw = ImageDraw.Draw(img)
        draw.ellipse([-40, -40, 160, 160], fill=(255, 255, 255, 22))
        draw.ellipse([120, 140, 300, 320], fill=(255, 255, 255, 18))
        buf = BytesIO()
        img.save(buf, format='PNG')
        user.profile_image.save(f'avatar_{user.username}.png', ContentFile(buf.getvalue()), save=True)

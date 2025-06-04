
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import Http404
from urllib.parse import unquote
from .models import CTFs, UserCTFProgress
import uuid
import mimetypes
from django.db.models.functions import Coalesce
from django.db.models import Value, IntegerField
from django.db.models import Sum, Min,Max, Value, IntegerField,Count
from .models import Comment
from .forms import CommentForm
from django.db.models import F, Case, When
from django.db.models import Sum, Count, Min, Max, Value, IntegerField, Case, When, F, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime
from datetime import datetime, timezone

# Import supabase client if available
try:
    from .supabase_client import supabase
except ImportError:
    supabase = None


# shows all ctf categories on /ctfs page
def ctf_list(request):
    ctftypes = CTFs.CTF_TYPE
    return render(request, 'ctfs/ctfs.html', {'ctftypes': ctftypes})


# shows all ctfs of a specific type
def ctf_type(request, type):
    type_upper = type.upper()
    ctf_type_dict = dict(CTFs.CTF_TYPE)

    if type_upper not in ctf_type_dict:
        raise Http404("CTF category not found")

    ctfs = CTFs.objects.filter(type=type_upper)
    return render(request, 'ctfs/ctf_type.html', {
        'ctfs': ctfs,
        'type': ctf_type_dict[type_upper]
    })

@login_required
def ctf_detail(request, type, title):
    type_upper = type.upper()
    
    # Decode the URL-encoded title parameter
    decoded_title = unquote(title)
    
    # Debug logging (remove in production)
    print(f"Original title: {title}")
    print(f"Decoded title: {decoded_title}")
    print(f"Looking for CTF with type: {type_upper}, title: {decoded_title}")
    
    try:
        ctf = CTFs.objects.get(type=type_upper, title=decoded_title)
    except CTFs.DoesNotExist:
        # Additional debug info
        print("CTF not found. Available CTFs:")
        for c in CTFs.objects.filter(type=type_upper):
            print(f"  - '{c.title}'")
        raise Http404("No CTFs matches the given query.")

    # Check if already solved
    solved = UserCTFProgress.objects.filter(user=request.user, ctf=ctf).exists()

    # Get comments and form
    comments = ctf.comments.order_by('-posted_at')
    form = CommentForm()

    if request.method == 'POST':
        # Handle answer submission
        if 'answer' in request.POST and 'comment_submit' not in request.POST:
            user_answer = request.POST.get('answer', '').strip()
            if user_answer.lower() == ctf.solution.lower():
                if solved:
                    messages.info(request, "You have already solved this challenge and received points.")
                else:
                    UserCTFProgress.objects.create(user=request.user, ctf=ctf, points_awarded=ctf.points)
                    messages.success(request, f"Correct answer! You earned {ctf.points} points.")
                return redirect('ctf_detail', type=type, title=title)
            else:
                messages.error(request, "Incorrect answer. Try again!")
                return redirect('ctf_detail', type=type, title=title)
        
        # Handle comment submission
        elif 'comment_submit' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.ctf = ctf
                comment.user = request.user
                comment.save()
                messages.success(request, "Comment added successfully.")
                return redirect('ctf_detail', type=type, title=title)

    return render(request, 'ctfs/ctf_details.html', {
        'ctf': ctf, 
        'solved': solved,
        'comments': comments,
        'form': form
    })
    

@login_required
def ctf_detail_slug(request, type, slug):
    type_upper = type.upper()
    ctf = get_object_or_404(CTFs, type=type_upper, slug=slug)
    solved = UserCTFProgress.objects.filter(user=request.user, ctf=ctf).exists()

    comments = ctf.comments.order_by('-posted_at')
    form = CommentForm()

    if request.method == 'POST':
        # Handle answer submission
        if 'answer' in request.POST or 'answer_submit' in request.POST:
            user_answer = request.POST.get('answer', '').strip()
            if user_answer.lower() == ctf.solution.lower():
                if solved:
                    messages.info(request, "You have already solved this challenge and received points.")
                else:
                    UserCTFProgress.objects.create(user=request.user, ctf=ctf, points_awarded=ctf.points)
                    messages.success(request, f"Correct answer! You earned {ctf.points} points.")
                return redirect('ctf_detail_slug', type=type, slug=slug)
            else:
                messages.error(request, "Incorrect answer. Try again!")
                return redirect('ctf_detail_slug', type=type, slug=slug)

        # Handle comment submission
        elif 'comment_submit' in request.POST:
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.ctf = ctf
                comment.user = request.user
                comment.save()
                messages.success(request, "Comment added successfully.")
                return redirect('ctf_detail_slug', type=type, slug=slug)

    return render(request, 'ctfs/ctf_details.html', {
        'ctf': ctf,
        'solved': solved,
        'comments': comments,
        'form': form
    })

@login_required
def leaderboard(request):
    # Get all users with basic annotations
    users = User.objects.annotate(
        total_points=Coalesce(Sum('userctfprogress__points_awarded'), Value(0), output_field=IntegerField()),
        solve_count=Count('userctfprogress', distinct=True),
        first_solve_time=Min('userctfprogress__solved_at'),
        last_solve_time=Max('userctfprogress__solved_at')
    )
    
    # Build leaderboard data with proper tiebreaking time
    leaderboard_data = []
    
    for user in users:
        if user.total_points > 0:
            # Get all solves for this user, ordered by time
            solves = list(user.userctfprogress_set.order_by('solved_at').values('points_awarded', 'solved_at'))
            
            # Find when they reached their current total
            running_total = 0
            time_reached_current_total = None
            
            for solve in solves:
                running_total += solve['points_awarded']
                if running_total == user.total_points:
                    time_reached_current_total = solve['solved_at']
                    break
        else:
            time_reached_current_total = None
        
        leaderboard_data.append({
            'user': user,
            'total_points': user.total_points,
            'solve_count': user.solve_count,
            'first_solve_time': user.first_solve_time,
            'last_solve_time': user.last_solve_time,
            'time_reached_current_total': time_reached_current_total
        })
    
    # Sort with proper tiebreaking
    leaderboard_data.sort(key=lambda x: (
        -x['total_points'],  # Higher points first
        x['time_reached_current_total'] if x['time_reached_current_total'] else datetime.max.replace(tzinfo=timezone.utc),  # Earlier time first
        x['user'].username  # Alphabetical for final tiebreak
    ))
    
    # Debug output
    print("Leaderboard Debug:")
    for i, data in enumerate(leaderboard_data[:10]):
        user = data['user']
        print(f"#{i+1}: {user.username} - {data['total_points']} points - "
              f"Reached current total: {data['time_reached_current_total']} - "
              f"First: {data['first_solve_time']} - Last: {data['last_solve_time']}")
    
    # Add the calculated fields back to user objects for template
    for data in leaderboard_data:
        user = data['user']
        user.total_points = data['total_points']
        user.solve_count = data['solve_count']
        user.time_reached_current_total = data['time_reached_current_total']
    
    return render(request, 'ctfs/leaderboard.html', {
        'leaderboard': [data['user'] for data in leaderboard_data]
    })


@login_required
def create_ctf(request):
    if not request.user.is_staff:
        messages.error(request, "Only admins can create CTFs.")
        return redirect('ctfs_url')

    if request.method == 'POST':
        title = request.POST.get('title')
        type = request.POST.get('type')
        category = request.POST.get('category')
        description = request.POST.get('description')
        date = request.POST.get('date')
        points = request.POST.get('points')
        solution = request.POST.get('solution')

        image_file = request.FILES.get('image')
        challenge_file = request.FILES.get('challenge_file')

        ctf = CTFs(
            title=title,
            type=type,
            category=category,
            description=description,
            date=date,
            points=points,
            solution=solution
        )

        # Image upload to Supabase (if configured)
        if image_file and supabase:
            try:
                image_ext = image_file.name.split('.')[-1]
                image_name = f"{uuid.uuid4()}.{image_ext}"
                mime_type = mimetypes.guess_type(image_name)[0] or "application/octet-stream"
                image_path = f"ctf-images/{image_name}"
                supabase.storage.from_("ctf-images").upload(image_path, image_file.read(), {"content-type": mime_type})
                image_url = supabase.storage.from_("ctf-images").get_public_url(image_path)
                ctf.image = image_url
            except Exception as e:
                messages.warning(request, f"Image upload failed: {e}")

        # Challenge file upload to Supabase (if configured)
        if challenge_file and supabase:
            try:
                file_ext = challenge_file.name.split('.')[-1]
                file_name = f"{uuid.uuid4()}.{file_ext}"
                mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
                file_path = f"ctf-files/{file_name}"
                supabase.storage.from_("ctf-files").upload(file_path, challenge_file.read(), {"content-type": mime_type})
                file_url = supabase.storage.from_("ctf-files").get_public_url(file_path)
                ctf.challange_files = file_url
            except Exception as e:
                messages.warning(request, f"File upload failed: {e}")

        ctf.save()
        messages.success(request, "CTF created successfully.")
        return redirect('ctfs_url')

    return render(request, 'ctfs/create_ctf.html', {
        'ctf_types': CTFs.CTF_TYPE,
        'categories': CTFs.CATEGORIES,
    })
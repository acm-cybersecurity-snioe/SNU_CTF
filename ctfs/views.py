# from django.shortcuts import render
# from .models import CTFs
# from .models import UserCTFProgress
# from django.shortcuts import get_object_or_404,redirect
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.models import User
# from django.db.models import Sum



# # shows all ctf categories on /ctfs page
# def ctf_list(request):
#     ctftypes = CTFs.CTF_TYPE  # gets all predefined ctf types from model
#     return render(request, 'ctfs/ctfs.html', {'ctftypes': ctftypes})  # sends it to template

# # shows all ctfs of a specific type
# def ctf_type(request, type):
#     type_upper = type.upper()  # converts url type to uppercase for matching
#     ctf_type_dict = dict(CTFs.CTF_TYPE)  # makes a dict from model choices

#     if type_upper not in ctf_type_dict:
#         raise Http404("CTF category not found")  # if type is invalid, return 404

#     ctfs = CTFs.objects.filter(type=type_upper)  # gets all ctfs of this type
#     return render(request, 'ctfs/ctf_type.html', {
#         'ctfs': ctfs,
#         'type': ctf_type_dict[type_upper]  # sends human-readable type name
#     })

# @login_required
# def ctf_detail(request, type, title):
#     type_upper = type.upper()
#     ctf = get_object_or_404(CTFs, type=type_upper, title=title)

#     if request.method == 'POST':
#         user_answer = request.POST.get('answer', '').strip()
#         # Assuming you store the correct solution in ctf.solution field
#         if user_answer.lower() == ctf.solution.lower():
#             # Check if user already solved it
#             already_solved = UserCTFProgress.objects.filter(user=request.user, ctf=ctf).exists()
#             if already_solved:
#                 messages.info(request, "You have already solved this challenge and received points.")
#             else:
#                 # Award points
#                 UserCTFProgress.objects.create(user=request.user, ctf=ctf, points_awarded=ctf.points)
#                 messages.success(request, f"Correct answer! You earned {ctf.points} points.")
#         else:
#             messages.error(request, "Incorrect answer. Try again!")

#         return redirect('ctf_detail', type=type, title=title)

#     return render(request, 'ctfs/ctf_details.html', {'ctf': ctf})

# @login_required
# def leaderboard(request):
#     leaderboard_data = (
#         User.objects
#         .annotate(total_points=Sum('userctfprogress__points_awarded'))
#         .order_by('-total_points')
#     )
#     return render(request, 'ctfs/leaderboard.html', {'leaderboard': leaderboard_data})
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from .models import CTFs, UserCTFProgress
from .supabase_client import supabase  # import Supabase client
import uuid  #for unique file names


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
    ctf = get_object_or_404(CTFs, type=type_upper, title=title)

    # Check if already solved
    solved = UserCTFProgress.objects.filter(user=request.user, ctf=ctf).exists()

    if request.method == 'POST':
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

    return render(request, 'ctfs/ctf_details.html', {'ctf': ctf, 'solved': solved})

@login_required
def leaderboard(request):
    leaderboard_data = (
        User.objects
        .annotate(total_points=Sum('userctfprogress__points_awarded'))
        .order_by('-total_points')
    )
    return render(request, 'ctfs/leaderboard.html', {'leaderboard': leaderboard_data})


#  NEW VIEW: create a CTF (Admin/Staff only)

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

        # Image upload to Supabase
        if image_file:
            image_ext = image_file.name.split('.')[-1]
            image_name = f"{uuid.uuid4()}.{image_ext}"
            mime_type = mimetypes.guess_type(image_name)[0] or "application/octet-stream"
            image_path = f"ctf-images/{image_name}"
            supabase.storage.from_("ctf-images").upload(image_path, image_file.read(), {"content-type": mime_type})
            image_url = supabase.storage.from_("ctf-images").get_public_url(image_path)
            ctf.image = image_url

        # Challenge file upload to Supabase
        if challenge_file:
            file_ext = challenge_file.name.split('.')[-1]
            file_name = f"{uuid.uuid4()}.{file_ext}"
            mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
            file_path = f"ctf-files/{file_name}"
            supabase.storage.from_("ctf-files").upload(file_path, challenge_file.read(), {"content-type": mime_type})
            file_url = supabase.storage.from_("ctf-files").get_public_url(file_path)
            ctf.challange_files = file_url

        ctf.save()
        messages.success(request, "CTF created successfully.")
        return redirect('ctfs_url')

    return render(request, 'ctfs/create_ctf.html', {
        'ctf_types': CTFs.CTF_TYPE,
        'categories': CTFs.CATEGORIES,
    })
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.accounts.forms import PersonalDataForm


@login_required
def personal_data(request):
    if request.method == "POST":
        form = PersonalDataForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Dados da sua conta atualizados com sucesso.")

            return redirect("accounts:profile")
    
    return render(request, "accounts/profile/personal_data.html", { "form": PersonalDataForm(instance=request.user) })
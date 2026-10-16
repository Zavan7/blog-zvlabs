"""Formulários do blog.

English:
    Blog forms.
"""

from django import forms

from blog.models import Comentario


class ComentarioForm(forms.ModelForm[Comentario]):
    """Formulário de comentário: o leitor só escreve o texto.

    Post, autor e status são definidos pelo backend e ficam fora de
    ``fields``, para ninguém forjar um comentário já aprovado.

    English:
        Comment form: the reader only writes the text.

        Post, author and status are set by the backend and stay out of
        ``fields``, so nobody can forge an already approved comment.
    """

    class Meta:
        """Só o texto é editável.

        English:
            Only the text is editable.
        """

        model = Comentario
        fields = ["texto"]
        labels = {"texto": "Seu comentário"}
        widgets = {"texto": forms.Textarea(attrs={"rows": 4})}

from rest_framework import serializers

from posts.models import Post, PostComment, PostVote


class PostPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        read_only = ('user',)
        exclude = ('created_at', 'updated_at', 'user', 'id')


class PostCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment

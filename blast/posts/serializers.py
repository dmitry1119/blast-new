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


class CommentPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        read_only = ('created_at', 'user', 'text', 'post',)


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ('text', 'post',)
from rest_framework import serializers

from posts.models import Post, PostComment, PostVote


class PostPublicSerializer(serializers.ModelSerializer):
    comments = serializers.ReadOnlyField(source='comments_count')
    votes = serializers.ReadOnlyField(source='votes_count')
    downvotes = serializers.ReadOnlyField(source='downvoted_count')

    class Meta:
        model = Post
        read_only = ('votes_count',)


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
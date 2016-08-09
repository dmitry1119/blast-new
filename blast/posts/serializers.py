from rest_framework import serializers

from posts.models import Post, PostComment, PostVote, PostReport


class PostPublicSerializer(serializers.ModelSerializer):
    comments = serializers.ReadOnlyField(source='comments_count')

    votes = serializers.ReadOnlyField(source='voted_count')
    downvotes = serializers.ReadOnlyField(source='downvoted_count')

    class Meta:
        model = Post
        read_only = ('comments', 'votes', 'downvotes')
        exclude = ('tags', 'voted_count', 'downvoted_count')


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        read_only = ('user',)
        fields = ('text', 'video', 'image', 'is_anonymous')


class ReportPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReport
        exclude = ('created_at', 'user', 'post',)


class CommentPublicSerializer(serializers.ModelSerializer):
    replies = serializers.ReadOnlyField(source='replies_count')

    class Meta:
        model = PostComment
        read_only = ('id', 'created_at', 'user', 'text', 'post', 'parent', 'replies_count')


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()

    class Meta:
        model = PostComment
        fields = ('id', 'text', 'post', 'parent',)


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVote
        fields = ('post', 'is_positive', )


class VotePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostVote

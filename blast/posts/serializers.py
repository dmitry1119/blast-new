from rest_framework import serializers

from posts.models import Post, PostComment, PostVote, PostReport


# TODO (VM): Exclude user for anonymous posts
class PostPublicSerializer(serializers.ModelSerializer):
    comments = serializers.ReadOnlyField(source='comments_count')
    image = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    votes = serializers.ReadOnlyField(source='voted_count')
    downvotes = serializers.ReadOnlyField(source='downvoted_count')

    image_135 = serializers.ImageField()
    image_248 = serializers.ImageField()

    def get_image(self, instance):
        request = self.context['request']
        if instance.image:
            return request.build_absolute_uri(instance.image.url)

        return None

    def get_video(self, instance):
        request = self.context['request']
        if instance.video:
            return request.build_absolute_uri(instance.video.url)

        return None

    class Meta:
        model = Post
        read_only = ('comments', 'votes', 'downvotes')
        exclude = ('tags', 'voted_count', 'downvoted_count',)


class PreviewPostSerializer(serializers.ModelSerializer):
    """Serializer with limited fields set for previewing in Notifications"""
    image_135 = serializers.ImageField()
    image_248 = serializers.ImageField()

    class Meta:
        model = Post
        fields = ('id', 'user', 'image', 'image_135', 'image_248',)


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

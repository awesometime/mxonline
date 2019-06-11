# encoding: utf-8
__author__ = 'mtianyan'
__date__ = '2018/1/13 0013 01:57'

# encoding: utf-8
from courses.views import CourseListView, CourseDetailView, CourseInfoView, CommentsView, AddCommentsView, VideoPlayView
from django.urls import path, re_path

app_name = "course"
urlpatterns = [
    # 课程列表url
    path('list/', CourseListView.as_view(), name="list"),

    # 课程详情页
    re_path('detail/(?P<course_id>\d+)/', CourseDetailView.as_view(), name="course_detail"),

    # 课程章节信息页
    re_path('info/(?P<course_id>\d+)/', CourseInfoView.as_view(), name="course_info"),

    # 课程评论页 ,展示已有评论
    re_path('comments/(?P<course_id>\d+)/', CommentsView.as_view(), name="course_comments"),

    # 新添加课程评论,已经把参数放到post当中了 不需要(?P<course_id>\d+)
    path('add_comment/', AddCommentsView.as_view(), name="add_comment"),

    # 课程视频播放页
    re_path('video/(?P<video_id>\d+)/', VideoPlayView.as_view(), name="video_play"),
]

# 某一总页面有其他页面的入口(url) 然后实现跳转

# course-detail.html页面配有{% url 'course:course_info' course.id %}
# 点击发现匹配到re_path('info/(?P<course_id>\d+)/', CourseInfoView.as_view(), name="course_info"),
# 就会进入CourseInfoView处理函数

# course-info.html页面配有{% url 'course:course_comments' course.id %}
# 点击发现匹配到re_path('comments/(?P<course_id>\d+)/', CommentsView.as_view(), name="course_comments"),
# 就会进入CommentsView处理函数

# 逻辑大概就是这样 一步步点击 一层层进入

# course-comments.html中一段ajax代码的理解
# todo 这里url是什么作用  需要了解一下ajax知识
# 点击发表评论按钮,Ajax向url:"{% url 'course:add_comment' %}", 发起一个request请求
# (此处为什么发起request请求,但url栏url地址没变成url 'course:add_comment,
# 我猜是ajax是异步请求, 所以url栏url地址不会变)
# urls控制器匹配到path('add_comment/', AddCommentsView.as_view(), name="add_comment"),
# 接下来去执行AddCommentsView处理函数 判断处理函数返回结果进行相应alert或者reload
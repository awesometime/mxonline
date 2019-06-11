from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.
from django.views.generic.base import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from courses.models import Course, CourseResource, Video
from operation.models import UserFavorite, CourseComments, UserCourse


"""
首页(base.html)顶部搜索栏搜索方法执行过程
三要素( 点击页面 | 触发js代码  | 将要发送请求的url ) (base.html | deco-common.js | request_url)
js前端代码执行 --> 后端处理函数执行 --> js前端代码执行
第一步:
    ajax代码在base.html里的deco-common.js 中的function search_click()函数
    用户在base.html  (base.html中有deco-common.js)
    中输入关键词以后js进行ajax处理,拼接url,然后发起一个相应ajax request请求, 请求中包含keywords

    js代码看到"course"就拼接出  request_url = "/course/list?keywords="+keywords,,并向它发送请求
    js代码看到"teacher"就拼接出 request_url = "/org/teacher/list?keywords="+keywords,并向它发送请求
    js代码看到"org"就拼接出     request_url = "/org/list?keywords="+keywords,并向它发送请求

第二步:
    urls控制器匹配到/course/list就进入courses app下的CourseListView处理函数中, 执行搜索功能的部分,
    具体是all_course.filter去数据库中过滤拿到符合要求的数据展示
    
    urls控制器匹配到/org/teacher/list就进入organization app下的TeacherListView处理函数中, 执行搜索功能的部分,
    具体是all_teacher.filter去数据库中过滤拿到符合要求的数据展示
    
    urls控制器匹配到/org/list就进入organization app下的OrgView处理函数中, 执行搜索功能的部分,
    具体是all_orgs.filter去数据库中过滤拿到符合要求的数据展示

第三步:
    js代码根据处理函数返回的结果进行异步alert或者reload等
"""
class CourseListView(View):
    def get(self, request):
        all_course = Course.objects.all()
        # 热门课程推荐
        hot_courses = Course.objects.all().order_by("-students")[:3]
        # 搜索功能
        # ajax代码在deco-common.js 中function search_click()
        search_keywords = request.GET.get('keywords', '')
        if search_keywords:
            # 在name字段进行操作,做like语句的操作。i代表不区分大小写
            # or操作使用Q
            all_course = all_course.filter(Q(name__icontains=search_keywords) | Q(
                desc__icontains=search_keywords) | Q(detail__icontains=search_keywords))
        # 对课程进行分页
        # 尝试获取前台get请求传递过来的page参数
        # 如果是不合法的配置参数默认返回第一页
        # 进行排序
        sort = request.GET.get('sort', "")
        if sort:
            if sort == "students":
                all_course = all_course.order_by("-students")
            elif sort == "hot":
                all_course = all_course.order_by("-click_nums")
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        # 这里指从all_org中取五个出来，每页显示5个
        p = Paginator(all_course, 6, request=request)
        courses = p.page(page)
        return render(request, "course-list.html", {
            "all_course": courses,
            "sort": sort,
            "hot_courses": hot_courses,
            "search_keywords": search_keywords
        })


class CourseDetailView(View):
    """课程详情处理view"""

    def get(self, request, course_id): # urls中传入course_id 此处接收该参数
        # 此处的id为表默认为我们添加的值。
        course = Course.objects.get(id=int(course_id))
        # 增加课程点击数
        course.click_nums += 1
        course.save()

        # 是否收藏课程
        has_fav_course = False
        has_fav_org = False

        # 必须是用户已登录我们才需要判断。
        if request.user.is_authenticated:
            if UserFavorite.objects.filter(
                    user=request.user, fav_id=course.id, fav_type=1):
                has_fav_course = True
            if UserFavorite.objects.filter(
                    user=request.user,
                    fav_id=course.course_org.id,
                    fav_type=2):
                has_fav_org = True
        # 取出标签找到标签相同的course
        tag = course.tag
        if tag:
            # 从1开始否则会推荐自己
            relate_courses = Course.objects.filter(tag=tag)[1:2]
        else:
            relate_courses = []
        return render(request, "course-detail.html", {
            "course": course,
            "relate_courses": relate_courses,
            "has_fav_course": has_fav_course,
            "has_fav_org": has_fav_org,
        })


class CourseInfoView(LoginRequiredMixin, View): # 继承LoginRequiredMixin保证在进入课程信息时是登录状态
    """处理课程章节信息页面的view"""
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request, course_id):
        # 此处的id为表默认为我们添加的值。
        course = Course.objects.get(id=int(course_id))

        # 查询用户是否开始学习了该课，如果还未学习则，加入用户课程表
        user_courses = UserCourse.objects.filter(
            user=request.user, course=course)
        if not user_courses:
            user_course = UserCourse(user=request.user, course=course)
            course.students += 1
            course.save()
            user_course.save()
        # 查询课程资源
        all_resources = CourseResource.objects.filter(course=course)
        # todo 这段逻辑 理解
        # 选出学了这门课的学生关系
        user_courses = UserCourse.objects.filter(course=course)
        # 从关系中取出user_id
        user_ids = [user_course.user_id for user_course in user_courses]
        # 这些用户学了的课程,外键会自动有id，取到字段
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        # 取出所有课程id,这个只是id,而不是queryset对象
        course_ids = [
            user_course.course_id for user_course in all_user_courses]
        # 获取学过该课程用户学过的其他课程, 根据课程id取到课程对象queryset
        relate_courses = Course.objects.filter(id__in=course_ids).order_by(
            "-click_nums").exclude(id=course.id)[:4]
        # 是否收藏课程
        return render(request, "course-video.html", {
            "course": course,
            "all_resources": all_resources,
            "relate_courses": relate_courses,
        })


class CommentsView(LoginRequiredMixin, View):# 继承LoginRequiredMixin保证在进入课程信息时是登录状态
    """评论视图"""
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request, course_id):
        # 此处的id为表默认为我们添加的值。
        course = Course.objects.get(id=int(course_id))
        all_resources = CourseResource.objects.filter(course=course)
        all_comments = CourseComments.objects.filter(
            course=course).order_by("-add_time")
        # 选出学了这门课的学生关系
        user_courses = UserCourse.objects.filter(course=course)
        # 从关系中取出user_id
        user_ids = [user_course.user_id for user_course in user_courses]
        # 这些用户学了的课程,外键会自动有id，取到字段 两个下划线___
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        # 取出所有课程id
        course_ids = [
            user_course.course_id for user_course in all_user_courses]
        # 获取学过该课程用户学过的其他课程
        relate_courses = Course.objects.filter(id__in=course_ids).order_by(
            "-click_nums").exclude(id=course.id)[:4]
        # 是否收藏课程
        return render(request, "course-comment.html", {
            "course": course,
            "all_resources": all_resources,
            "all_comments": all_comments,
            "relate_courses": relate_courses,
        })


"""
# course-comment.html中的一段【关于发表评论】的js代码
# js代码里的url:"{% url 'course:add_comment' %}"这一条是什么作用:  需要了解一下ajax知识
# 第1步:
# 在course-comment.html页面点击发表评论按钮,js代码发挥作用,Ajax向url:/course/add_comment/,
# 发起一个带着comment内容的post request请求
# (此处为什么发起request请求,但url栏url地址没变成url 'course:add_comment,我猜是ajax是异步请求所以
# url栏url地址不会变)
# 第2步:
# urls控制器匹配到path('add_comment/', AddCommentsView.as_view(), name="add_comment"),
# 接下来去执行AddCommentsView处理函数,从请求中获取comment内容,判断处理函数返回结果进行相应alert或者reload
"""
class AddCommentsView(View):
    """ajax方式添加评论"""
    def post(self, request):
        if not request.user.is_authenticated:
            # 未登录时返回json提示未登录，跳转到登录页面是在ajax中做的
            return HttpResponse(
                '{"status":"fail", "msg":"用户未登录"}',
                content_type='application/json')
        course_id = request.POST.get("course_id", 0)
        comments = request.POST.get("comments", "")
        # todo 理解一下if里保存评论到数据库的代码
        if int(course_id) > 0 and comments:
            course_comments = CourseComments()
            # get只能取出一条数据，如果有多条抛出异常。没有数据也抛异常
            # filter取一个列表出来，queryset。没有数据返回空的queryset不会抛异常
            course = Course.objects.get(id=int(course_id))
            # 外键存入要存入对象
            course_comments.course = course
            course_comments.comments = comments
            course_comments.user = request.user
            course_comments.save()
            return HttpResponse(
                '{"status":"success", "msg":"评论成功"}',
                content_type='application/json')
        else:
            return HttpResponse(
                '{"status":"fail", "msg":"评论失败"}',
                content_type='application/json')


class VideoPlayView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request, video_id):
        # 此处的id为表默认为我们添加的值。
        video = Video.objects.get(id=int(video_id))
        # 找到对应的course
        course = video.lesson.course
        # 查询用户是否开始学习了该课，如果还未学习则，加入用户课程表
        user_courses = UserCourse.objects.filter(
            user=request.user, course=course)
        if not user_courses:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()
        # 查询课程资源
        all_resources = CourseResource.objects.filter(course=course)
        # 选出学了这门课的学生关系
        user_courses = UserCourse.objects.filter(course=course)
        # 从关系中取出user_id
        user_ids = [user_course.user_id for user_course in user_courses]
        # 这些用户学了的课程,外键会自动有id，取到字段
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        # 取出所有课程id
        course_ids = [
            user_course.course_id for user_course in all_user_courses]
        # 获取学过该课程用户学过的其他课程
        relate_courses = Course.objects.filter(id__in=course_ids).order_by(
            "-click_nums").exclude(id=course.id)[:4]
        # 是否收藏课程
        return render(request, "course-play.html", {
            "course": course,
            "all_resources": all_resources,
            "relate_courses": relate_courses,
            "video": video,
        })

# todo 说明
# course-video.html是展示该课程所有章节视频资料的页面,course-play.html是播放具体某个视频的页面
from django.utils.crypto import get_random_string
from django.views import View

from Base.common import deprint
from Base.error import Error
from Base.policy import get_avatar_policy
from Base.qn import QN_PUBLIC_MANAGER
from Base.response import response, error_response
from Base.validator import require_get, require_json, require_post
from Image.models import Image


MLC_KEYS = ['sheng', 'ming', 'lastword']
MLC_KEYS.reverse()
TEMPLATE = 'engif/attention/%s.png'
MLC_IMG_LIST = []
for k in MLC_KEYS:
    MLC_IMG_LIST.append(dict(key=TEMPLATE % k))
MLC_IMG_COUNT = len(MLC_KEYS)

MLC_IMG_DICT = dict(
    image_list=MLC_IMG_LIST,
    count=MLC_IMG_COUNT,
    next=0,
)


class ImageHistoryView(View):
    @staticmethod
    @require_get([{
        'value': 'end',
        'default': True,
        'default_value': -1,
        'process': int,
    }, {
        'value': 'count',
        'default': True,
        'default_value': 10,
        'process': int,
    }])
    def get(request):
        """ GET /api/image/history

        获取历史图片
        """

        end = request.d.end
        count = request.d.count
        image_list = Image.get_old_images(end, count)

        if end == -1:
            image_list['image_list'] += MLC_IMG_LIST
            image_list['count'] += MLC_IMG_COUNT
        return response(body=image_list)


class ImageView(View):
    @staticmethod
    @require_get(
        # [{
        #     'value': 'num',
        #     'default': True,
        #     'default_value': 1,
        #     'process': int,
        # }]
    )
    # @require_login
    # @require_scope(deny_all_auth_token=True)
    def get(request):
        """ GET /api/image/

        获取七牛上传token
        """
        # o_user = request.user
        # filename = request.d.filename

        # if not isinstance(o_user, User):
        #     return error_response(Error.STRANGE)
        # num = request.d.num
        # if num < 1:
        #     num = 1
        # if num > 9:
        #     num = 9

        import datetime
        token_list = []

        for _ in range(1):
            crt_time = datetime.datetime.now().timestamp()
            key = '%s_%s' % (crt_time, get_random_string(length=4))
            qn_token, key = QN_PUBLIC_MANAGER.get_upload_token(key, get_avatar_policy())
            token_list.append(dict(upload_token=qn_token, key=key))
        return response(body=token_list[0])

    @staticmethod
    @require_json
    @require_post(['key'])
    def post(request):
        """ POST /api/image/

        七牛上传用户头像回调函数
        """
        deprint('ImageView-post')
        ret = QN_PUBLIC_MANAGER.qiniu_auth_callback(request)
        if ret.error is not Error.OK:
            return error_response(ret)

        key = request.d.key
        ret = Image.create(key)
        if ret.error is not Error.OK:
            return error_response(ret)
        o_image = ret.body
        if not isinstance(o_image, Image):
            return error_response(Error.STRANGE)

        return response(body=o_image.to_dict())

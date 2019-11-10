from marshmallow import Schema, fields, post_dump
from marshmallow_union import Union


class GitSrcSchema(Schema):
    url = fields.Url(data_key="git")
    rev = fields.Str(missing="")


class DerivationsSchema(Schema):
    srcs = fields.Dict(keys=fields.Str(), values=Union([fields.Nested(GitSrcSchema)]))

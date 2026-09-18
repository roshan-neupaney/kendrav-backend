from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from urllib.parse import urlparse, parse_qs

class StandardCursorPagination(CursorPagination):
    page_size=20
    page_size_query_param='page_size'
    max_page_size = 100
    ordering='id'

    def get_paginated_response(self, data):
        next_link = self.get_next_link()

        next_cursor = None

        if next_link:
            parsed = urlparse(next_link)
            next_cursor = parse_qs(parsed.query).get('cursor', None)[0]

        return Response({
            "next_cursor": next_cursor,
            "has_more": next_link is not None,
            "limit": self.page_size,
            "result": data
        })
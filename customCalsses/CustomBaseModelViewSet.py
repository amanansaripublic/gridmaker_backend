
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

class CustomBaseModelViewSet_ChoicesMixin:
    @action(detail=False, methods=['get'], url_path='choices', url_name='choices')
    def choices(self, request, *args, **kwargs):
        model = self.queryset.model
        choices = {}
        
        # Iterate over all fields in the model
        for field in model._meta.fields:
            if field.choices:
                # Add the field name and its choices to the response
                choices[field.name + "_choices"] = [{'key': key, 'value': value} for key, value in field.choices]
        
        return Response(choices)
    
    def retrieve(self, request, *args, **kwargs):
        # Call the original retrieve method
        response = super().retrieve(request, *args, **kwargs)
        
        # Check if the 'model_choices' query parameter is present and true
        include_choices = request.query_params.get('get_model_choices', 'false').lower() == 'true'
        
        if include_choices:
            # Get the model from the queryset
            model = self.queryset.model
            
            # Dynamically add choices fields to the response
            choices = {}
            for field in model._meta.fields:
                if field.choices:
                    choices[field.name + "_choices"] = [
                        {"key": key, "value": value} for key, value in field.choices
                    ]
            
            # Update the response data with choices
            response.data.update(choices)
        
        return response



class CustomBaseModelViewSet(CustomBaseModelViewSet_ChoicesMixin, ModelViewSet):
    pass


# class ChoicesMixin:
#     @action(detail=False, methods=['get'], url_path='choices', url_name='choices')
#     def choices(self, request, *args, **kwargs):
#         model = self.queryset.model
#         choices = {}
        
#         # Iterate over all fields in the model
#         for field in model._meta.fields:
#             if field.choices:
#                 # If the field has choices, check if they include a color
#                 field_choices = []
#                 for choice in model.STATUS_CHOICES:
#                     if len(choice) == 3:  # Includes color
#                         field_choices.append({
#                             'key': choice[0],
#                             'label': choice[1],
#                             'color': choice[2]
#                         })
#                     else:
#                         field_choices.append({
#                             'key': choice[0],
#                             'label': choice[1],
#                         })
#                 choices[field.name] = field_choices
        
#         return Response(choices)

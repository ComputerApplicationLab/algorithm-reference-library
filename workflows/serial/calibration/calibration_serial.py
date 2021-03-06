"""

"""

from processing_components.calibration.calibration_control import calibrate_function
from processing_components.calibration.operations import apply_gaintable
from processing_components.visibility.gather_scatter import visibility_gather_channel
from processing_components.visibility.operations import divide_visibility, integrate_visibility_by_channel


def calibrate_list_serial_workflow(vis_list, model_vislist, calibration_context='TG', global_solution=True,
                                   **kwargs):
    """ Create a set of components for (optionally global) calibration of a list of visibilities

    If global solution is true then visibilities are gathered to a single visibility data set which is then
    self-calibrated. The resulting gaintable is then effectively scattered out for application to each visibility
    set. If global solution is false then the solutions are performed locally.

    :param vis_list:
    :param model_vislist:
    :param calibration_context: String giving terms to be calibrated e.g. 'TGB'
    :param global_solution: Solve for global gains
    :param kwargs: Parameters for functions in components
    :return:
    """
    
    def solve_and_apply(vis, modelvis=None):
        return calibrate_function(vis, modelvis, calibration_context=calibration_context, **kwargs)[0]
    
    if global_solution:
        point_vislist = [divide_visibility(vis_list[i], model_vislist[i])
                         for i, _ in enumerate(vis_list)]
        global_point_vis_list = visibility_gather_channel(point_vislist)
        global_point_vis_list = integrate_visibility_by_channel(global_point_vis_list)
        # This is a global solution so we only compute one gain table
        _, gt_list = solve_and_apply(global_point_vis_list)
        return [apply_gaintable(v, gt_list, inverse=True)
                for v in vis_list]
    else:
        
        return [solve_and_apply(vis_list[i], model_vislist[i]) for i, v in enumerate(vis_list)]

package demo.tracking;

import org.mapstruct.Mapper;

@Mapper
public interface SampleStatusMapper {

    String mapStatus(String rawStatus);
}
